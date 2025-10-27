const API_BASE_URL = "http://127.0.0.1:8000"

export interface ChatSession {
  session_id: string
}

export interface ChatMessage {
  sender: "human" | "ai" | "tool"
  content: string
  timestamp?: number
}

export interface ChatResponse {
  conversation: [string, string]
}

export interface MessagesResponse {
  message: ChatMessage[]
}

export interface SessionsResponse {
  session_ids: string[]
}

export interface StreamChunk {
  type: "content" | "done" | "error"
  content?: string
  error?: string
}

class RealChatAPI {
  private async handleResponse<T>(response: Response): Promise<T> {
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`API Error ${response.status}: ${errorText}`)
    }

    if (response.status === 204) {
      return { success: true } as T
    }

    return response.json()
  }

  async createNewChat(): Promise<ChatSession> {
    console.log("[API] Creating new chat session...")
    const response = await fetch(`${API_BASE_URL}/new_chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
    })

    const result = await this.handleResponse<ChatSession>(response)
    console.log("[API] New session created:", result.session_id)
    return result
  }

  // NEW: Streaming chat with SSE
  async sendMessageStream(
    sessionId: string,
    userInput: string,
    onChunk: (chunk: StreamChunk) => void
  ): Promise<void> {
    console.log("[API] Starting streaming chat for session:", sessionId)
    
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "text/event-stream",
      },
      body: JSON.stringify({
        session_id: sessionId,
        user_input: userInput,
      }),
    })

    if (!response.ok) {
      throw new Error(`API Error ${response.status}`)
    }

    const reader = response.body?.getReader()
    const decoder = new TextDecoder()

    if (!reader) {
      throw new Error("No response body")
    }

    try {
      let buffer = ""
      
      while (true) {
        const { done, value } = await reader.read()
        
        if (done) {
          onChunk({ type: "done" })
          break
        }

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        
        // Keep incomplete line in buffer
        buffer = lines.pop() || ""

        for (const line of lines) {
          const trimmed = line.trim()
          if (trimmed.startsWith("data: ")) {
            try {
              const jsonStr = trimmed.slice(6)
              const data = JSON.parse(jsonStr)
              
              // Handle different event types from backend
              if (data.type === "content") {
                onChunk({ type: "content", content: data.content })
              } else if (data.type === "tool_call") {
                onChunk({ type: "content", content: `\n[Using tool: ${data.tool}]\n` })
              } else if (data.type === "tool_result") {
                onChunk({ type: "content", content: `\n${data.content}\n` })
              } else if (data.type === "end") {
                onChunk({ type: "done" })
              } else if (data.type === "error") {
                onChunk({ type: "error", error: data.message })
              }
            } catch (e) {
              console.error("[API] Failed to parse SSE data:", e, "Line:", trimmed)
            }
          }
        }
      }
    } finally {
      reader.releaseLock()
    }
  }

  // Legacy non-streaming method (kept for compatibility)
  async sendMessage(sessionId: string, userInput: string): Promise<ChatResponse> {
    console.log("[API] Sending message to session:", sessionId)
    const response = await fetch(`${API_BASE_URL}/chat`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify({
        session_id: sessionId,
        user_input: userInput,
      }),
    })
    
    const result = await this.handleResponse<{conversation: [string, string]}>(response)
    console.log("[API] Received AI response")
    
    return {
      conversation: result.conversation || [userInput, "No response received"],
    }
  }

  // NEW: Upload file
  async uploadFile(file: File): Promise<string> {
    console.log("[API] Uploading file:", file.name)
    
    const formData = new FormData()
    formData.append("file", file)

    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: "POST",
      body: formData,
    })

    if (!response.ok) {
      throw new Error(`Upload failed: ${response.status}`)
    }

    const result = await response.text()
    console.log("[API] File uploaded:", result)
    return result
  }

  // NEW: Download file
  async downloadFile(path: string): Promise<Blob> {
    console.log("[API] Downloading file:", path)
    
    const response = await fetch(`${API_BASE_URL}/download?path=${encodeURIComponent(path)}`, {
      method: "GET",
    })

    if (!response.ok) {
      throw new Error(`Download failed: ${response.status}`)
    }

    return response.blob()
  }

  async getAllSessions(): Promise<SessionsResponse> {
    console.log("[API] Fetching all sessions...")
    const response = await fetch(`${API_BASE_URL}/session_id`, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    })

    const result = await this.handleResponse<SessionsResponse>(response)
    console.log("[API] Found sessions:", result.session_ids.length)
    return result
  }

  async getMessagesBySession(sessionId: string): Promise<MessagesResponse> {
    console.log("[API] Fetching messages for session:", sessionId)
    const response = await fetch(`${API_BASE_URL}/messages_by_session_id?session_id=${sessionId}`, {
      method: "GET",
      headers: {
        Accept: "application/json",
      },
    })

    const result = await this.handleResponse<MessagesResponse>(response)
    console.log("[API] Found messages:", result.message.length)
    return result
  }

  async deleteSession(sessionId: string): Promise<{ success: boolean }> {
    console.log("[API] Deleting session:", sessionId)
    const response = await fetch(`${API_BASE_URL}/delete_by_session_id?session_id=${sessionId}`, {
      method: "DELETE",
      headers: {
        Accept: "application/json",
      },
    })

    const result = await this.handleResponse<{ success: boolean }>(response)
    console.log("[API] Session deleted successfully")
    return result
  }
}

export const chatAPI = new RealChatAPI()