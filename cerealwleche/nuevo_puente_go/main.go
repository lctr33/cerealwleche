// main.go (Versión con correcciones de compilación)
package main

import (
	"context"
	"database/sql"
	"encoding/json"
	"fmt"
	"net/http"
	"os"
	"os/signal"
	// "strings" // Se elimina esta línea porque no se usa
	"syscall"

	"github.com/mdp/qrterminal/v3"

	"go.mau.fi/whatsmeow"
	waProto "go.mau.fi/whatsmeow/binary/proto"
	"go.mau.fi/whatsmeow/store/sqlstore"
	"go.mau.fi/whatsmeow/types"
	"go.mau.fi/whatsmeow/types/events"
	waLog "go.mau.fi/whatsmeow/util/log"

	_ "github.com/mattn/go-sqlite3"
	"google.golang.org/protobuf/proto"
)

var messageDB *sql.DB
var client *whatsmeow.Client

type SendMessageRequest struct {
	Recipient string `json:"recipient"`
	Message   string `json:"message"`
}

type SendMessageResponse struct {
	Success bool   `json:"success"`
	Message string `json:"message"`
}

func handleSendMessage(w http.ResponseWriter, r *http.Request) {
	var req SendMessageRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, err.Error(), http.StatusBadRequest)
		return
	}

    // --- LÓGICA CORREGIDA PARA MANEJAR ERRORES ---
	recipientJID, err := types.ParseJID(req.Recipient)
	if err != nil { // La forma correcta de checar el error
		http.Error(w, "Invalid recipient JID", http.StatusBadRequest)
		return
	}
    // --- FIN DE LA CORRECCIÓN ---

	msg := &waProto.Message{Conversation: proto.String(req.Message)}
	_, err = client.SendMessage(context.Background(), recipientJID, msg)

	var resp SendMessageResponse
	if err != nil {
		resp = SendMessageResponse{Success: false, Message: err.Error()}
		w.WriteHeader(http.StatusInternalServerError)
	} else {
		resp = SendMessageResponse{Success: true, Message: "Message sent successfully"}
		w.WriteHeader(http.StatusOK)
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(resp)
}


// Reemplaza tu función eventHandler con esta versión final
func eventHandler(evt interface{}) {
	switch v := evt.(type) {
	case *events.Message:
		var messageContent string
		if v.Message.GetConversation() != "" {
			messageContent = v.Message.GetConversation()
		} else if extendedMsg := v.Message.GetExtendedTextMessage(); extendedMsg != nil {
			messageContent = extendedMsg.GetText()
		} else {
			fmt.Println("Evento de mensaje recibido, pero sin contenido textual. Ignorando.")
			return
		}

		fmt.Println("---------------------------------")
		fmt.Println("¡Mensaje de Usuario Recibido!")
		fmt.Printf("De: %s\n", v.Info.Sender)
		fmt.Printf("Contenido: %s\n", messageContent)

		// --- INICIO DE LÓGICA DE TRANSACCIÓN ---
		tx, err := messageDB.Begin()
		if err != nil {
			fmt.Printf("Error al iniciar la transacción: %v\n", err)
			return
		}
		// Si algo sale mal, 'defer tx.Rollback()' deshará la transacción
		defer tx.Rollback()

		// Paso 1: Guardar o actualizar el CHAT
		_, err = tx.Exec(`
			INSERT INTO chats (jid, name, last_message_time) VALUES (?, ?, ?)
			ON CONFLICT(jid) DO UPDATE SET name=excluded.name, last_message_time=excluded.last_message_time
		`, v.Info.Chat.String(), v.Info.PushName, v.Info.Timestamp)
		if err != nil {
			fmt.Printf("Error al guardar el chat en la transacción: %v\n", err)
			return
		}

		// Paso 2: Guardar el MENSAJE
		_, err = tx.Exec(`
			INSERT INTO messages (id, chat_jid, sender, content, timestamp, is_from_me)
			VALUES (?, ?, ?, ?, ?, ?)
			ON CONFLICT(id) DO NOTHING
		`, v.Info.ID, v.Info.Chat.String(), v.Info.Sender.String(), messageContent, v.Info.Timestamp, v.Info.IsFromMe)
		if err != nil {
			fmt.Printf("Error al guardar el mensaje en la transacción: %v\n", err)
			return
		}

		// Si todo fue bien, confirmamos la transacción
		err = tx.Commit()
		if err != nil {
			fmt.Printf("Error al confirmar la transacción: %v\n", err)
		} else {
			fmt.Println("¡Mensaje guardado en la base de datos local (con transacción)!")
		}
		// --- FIN DE LÓGICA DE TRANSACCIÓN ---
		fmt.Println("---------------------------------")
	}
}

func initMessageDB() {
	var err error
	messageDB, err = sql.Open("sqlite3", "file:messages.db?_foreign_keys=on")
	if err != nil {
		panic(fmt.Sprintf("No se pudo abrir la base de datos de mensajes: %v", err))
	}

	createTableSQL := `
	CREATE TABLE IF NOT EXISTS chats (
		jid TEXT PRIMARY KEY,
		name TEXT,
		last_message_time TIMESTAMP
	);
	CREATE TABLE IF NOT EXISTS messages (
		id TEXT PRIMARY KEY,
		chat_jid TEXT,
		sender TEXT,
		content TEXT,
		timestamp TIMESTAMP,
		is_from_me BOOLEAN,
		FOREIGN KEY (chat_jid) REFERENCES chats (jid)
	);`
	_, err = messageDB.Exec(createTableSQL)
	if err != nil {
		panic(fmt.Sprintf("No se pudo crear la tabla de mensajes: %v", err))
	}
	fmt.Println("Base de datos de mensajes lista.")
}

func main() {
	initMessageDB()
	dbLog := waLog.Stdout("Database", "DEBUG", true)
	ctx := context.Background()
	container, err := sqlstore.New(ctx, "sqlite3", "file:session.db?_foreign_keys=on", dbLog)
	if err != nil { panic(err) }
	deviceStore, err := container.GetFirstDevice(ctx)
	if err != nil { panic(err) }

	clientLog := waLog.Stdout("Client", "DEBUG", true)
	client = whatsmeow.NewClient(deviceStore, clientLog)
	client.AddEventHandler(eventHandler)

	http.HandleFunc("/api/send", handleSendMessage)
	fmt.Println("Iniciando servidor API en el puerto 8080...")
	go func() {
		if err := http.ListenAndServe(":8080", nil); err != nil {
			fmt.Printf("Error iniciando servidor API: %v\n", err)
		}
	}()

	if client.Store.ID == nil {
		qrChan, _ := client.GetQRChannel(context.Background())
		err = client.Connect()
		if err != nil { panic(err) }
		for evt := range qrChan {
			if evt.Event == "code" {
				fmt.Println("Escanea el código QR con tu teléfono:")
				qrterminal.GenerateHalfBlock(evt.Code, qrterminal.L, os.Stdout)
			} else {
				fmt.Println("Evento de Login:", evt.Event)
			}
		}
	} else {
		err = client.Connect()
		if err != nil { panic(err) }
		fmt.Println("Conectado usando sesión existente.")
	}

	c := make(chan os.Signal, 1)
	signal.Notify(c, os.Interrupt, syscall.SIGTERM)
	<-c

	client.Disconnect()
	messageDB.Close()
}