"use client"

import { motion, AnimatePresence } from "framer-motion"
import { ChatWindow } from "@/components/chat-window"
import { MessageInput } from "@/components/message-input"
import { SessionSelector } from "@/components/session-selector"
import { useChat } from "@/hooks/use-chat"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { AlertCircle, X, Plus, MessageSquare, ChevronLeft, ChevronRight } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { useState, useEffect } from "react"

export default function ChatPage() {
  const {
    currentSessionId,
    messages,
    isLoading,
    error,
    uploadProgress,
    createNewSession,
    loadSession,
    sendMessageWithAutoSession,
    uploadFile,
    clearSession,
    clearError,
  } = useChat()

  const [sidebarOpen, setSidebarOpen] = useState(true)
  const [currentTime, setCurrentTime] = useState("")
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
    setCurrentTime(new Date().toLocaleString())
    
    const interval = setInterval(() => {
      setCurrentTime(new Date().toLocaleString())
    }, 60000)

    return () => clearInterval(interval)
  }, [])

  const handleNewSession = async () => {
    try {
      await createNewSession()
    } catch (err) {
      console.error("Failed to create new session:", err)
    }
  }

  const handleSessionChange = async (sessionId: string | null) => {
    if (sessionId) {
      try {
        await loadSession(sessionId)
      } catch (err) {
        console.error("Failed to load session:", err)
      }
    } else {
      clearSession()
    }
  }

  const handleSendMessage = async (message: string) => {
    try {
      await sendMessageWithAutoSession(message, true)
    } catch (err) {
      console.error("Failed to send message:", err)
    }
  }

  const handleFileUpload = async (file: File) => {
    try {
      await uploadFile(file)
    } catch (err) {
      console.error("Failed to upload file:", err)
      throw err
    }
  }

  return (
    <div className="h-screen flex bg-gradient-to-br from-gray-50 via-white to-blue-50">
      {/* SIDEBAR */}
      <div 
        className={`relative transition-all duration-300 ease-in-out bg-white border-r border-gray-200 shadow-lg ${
          sidebarOpen ? 'w-80' : 'w-16'
        }`}
      >
        <div className="absolute -right-4 top-6 z-50">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="bg-white border-gray-300 shadow-md hover:shadow-lg rounded-full h-8 w-8 p-0 flex items-center justify-center"
          >
            {sidebarOpen ? (
              <ChevronLeft className="h-4 w-4 text-gray-600" />
            ) : (
              <ChevronRight className="h-4 w-4 text-gray-600" />
            )}
          </Button>
        </div>

        <div className="h-full flex flex-col">
          <div className="p-4 border-b border-gray-200">
            <div className="flex items-center gap-3 mb-4">
              <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-600 rounded-lg shadow-sm flex-shrink-0">
                <MessageSquare className="w-5 h-5 text-white" />
              </div>
              
              <AnimatePresence>
                {sidebarOpen && (
                  <motion.div
                    initial={{ opacity: 0, width: 0 }}
                    animate={{ opacity: 1, width: "auto" }}
                    exit={{ opacity: 0, width: 0 }}
                    className="overflow-hidden"
                  >
                    <div>
                      <h1 className="text-lg font-bold text-gray-800 whitespace-nowrap">AI Chat</h1>
                      <p className="text-xs text-gray-500 whitespace-nowrap">Intelligent Assistant</p>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            <AnimatePresence>
              {sidebarOpen ? (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: "auto" }}
                  exit={{ opacity: 0, height: 0 }}
                  className="overflow-hidden"
                >
                  <Button
                    onClick={handleNewSession}
                    className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-md hover:shadow-lg transition-all duration-200"
                    disabled={isLoading}
                  >
                    <Plus className="w-4 h-4 mr-2" />
                    New Chat
                  </Button>
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="flex justify-center"
                >
                  <Button
                    onClick={handleNewSession}
                    size="sm"
                    className="bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white w-10 h-10 p-0"
                    disabled={isLoading}
                  >
                    <Plus className="w-4 h-4" />
                  </Button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>

          <AnimatePresence>
            {sidebarOpen && currentSessionId && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="mx-4 mt-4 overflow-hidden"
              >
                <div className="p-3 bg-gray-50 rounded-lg border">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">Current Session</span>
                    <Badge variant="secondary" className="text-xs">
                      {messages.length} messages
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-500 mt-1 font-mono">
                    {currentSessionId.length > 20 ? `${currentSessionId.slice(0, 20)}...` : currentSessionId}
                  </p>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          <div className="flex-1 overflow-hidden">
            <AnimatePresence>
              {sidebarOpen ? (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  exit={{ opacity: 0 }}
                  className="p-4 h-full"
                >
                  <SessionSelector
                    currentSessionId={currentSessionId}
                    onSessionChange={handleSessionChange}
                    onNewSession={() => {}}
                  />
                </motion.div>
              ) : (
                <motion.div
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="p-2 flex flex-col items-center gap-2 mt-4"
                >
                  <div className="w-8 h-8 bg-gray-100 rounded-lg flex items-center justify-center">
                    <MessageSquare className="w-4 h-4 text-gray-600" />
                  </div>
                  <div className="w-8 h-1 bg-gray-300 rounded-full"></div>
                  <div className="w-8 h-1 bg-gray-200 rounded-full"></div>
                  <div className="w-8 h-1 bg-gray-200 rounded-full"></div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>

      {/* MAIN CONTENT */}
      <div className="flex-1 flex flex-col min-w-0">
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          className="bg-white/80 backdrop-blur-sm border-b border-gray-200 p-4 flex-shrink-0"
        >
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-800">
                {currentSessionId ? 'Chat Session' : 'Welcome to AI Chat'}
              </h2>
              <p className="text-sm text-gray-600">
                {currentSessionId 
                  ? `${messages.length} messages • ${isLoading ? 'AI is thinking...' : 'Ready to chat'}`
                  : 'Start a new conversation or select an existing session'
                }
              </p>
            </div>

            <div className="flex items-center gap-3">
              {isLoading && (
                <Badge variant="secondary" className="animate-pulse">
                  <div className="w-2 h-2 bg-blue-500 rounded-full animate-bounce mr-2"></div>
                  Processing
                </Badge>
              )}
              {/* <div className="flex items-center gap-1 text-xs text-gray-500">
                <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                <span>Streaming Enabled</span>
              </div> */}
            </div>
          </div>
        </motion.div>

        <AnimatePresence>
          {error && (
            <motion.div
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              className="mx-4 mt-4 flex-shrink-0"
            >
              <Alert className="border-red-200 bg-red-50">
                <AlertCircle className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800 flex items-center justify-between">
                  <span>{error}</span>
                  <Button
                    onClick={clearError}
                    size="sm"
                    variant="ghost"
                    className="h-6 w-6 p-0 text-red-600 hover:text-red-700 hover:bg-red-100 rounded-full"
                  >
                    <X className="h-3 w-3" />
                  </Button>
                </AlertDescription>
              </Alert>
            </motion.div>
          )}
        </AnimatePresence>

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.2 }}
          className="flex-1 flex flex-col bg-white mx-4 my-4 rounded-2xl shadow-lg border border-gray-200 overflow-hidden min-h-0"
        >
          <div className="flex-1 min-h-0">
            <ChatWindow messages={messages} isLoading={isLoading} />
          </div>

          <div className="border-t border-gray-200 bg-gray-50/50 p-4 flex-shrink-0">
            <MessageInput
              onSendMessage={handleSendMessage}
              onFileUpload={handleFileUpload}
              disabled={isLoading}
              uploadProgress={uploadProgress}
              placeholder={
                currentSessionId
                  ? isLoading
                    ? "AI is thinking..."
                    : "Type your message here..."
                  : "Start a new chat to begin messaging..."
              }
            />
          </div>
        </motion.div>

        <div className="px-4 py-3 bg-white/80 backdrop-blur-sm border-t border-gray-200 flex-shrink-0">
          <div className="flex items-center justify-between text-xs text-gray-500">
            <div className="flex items-center gap-4">
              <span className="font-medium">AI Assistant v1.0</span>
              <span>•</span>
              <span>{messages.length} total messages</span>
            </div>
            <div className="text-xs">
              {mounted ? currentTime : "Loading..."}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}