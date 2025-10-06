"use client"

import { useEffect, useRef } from "react"
import { ChatMessage } from "./chat-message"
import { motion } from "framer-motion"
import type { ChatMessage as ChatMessageType } from "@/lib/api"

interface ChatWindowProps {
  messages: ChatMessageType[]
  isLoading?: boolean
}

export function ChatWindow({ messages, isLoading }: ChatWindowProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  return (
    <div 
      ref={containerRef}
      className="h-full overflow-y-auto p-6 space-y-4"
      style={{ 
        maxHeight: '100%',
        overflowY: 'auto',
        scrollBehavior: 'smooth'
      }}
    >
      {/* Empty State */}
      {messages.length === 0 && !isLoading && (
        <div className="h-full flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 bg-gradient-to-r from-blue-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
              </svg>
            </div>
            <h3 className="text-xl font-semibold text-gray-800 mb-2">Welcome to AI Chat</h3>
            <p className="text-gray-600 mb-4">Start a conversation with the intelligent reasoning agent</p>
            {/* <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-50 rounded-lg"> */}
              {/* <span className="text-sm text-blue-700">✨ Streaming enabled</span>
              <span className="text-sm text-blue-700">📎 File upload ready</span> */}
            {/* </div> */}
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="space-y-4">
        {messages.map((message, index) => (
          <ChatMessage
            key={`${message.timestamp || Date.now()}-${index}`}
            sender={message.sender}
            content={message.content}
            index={index}
          />
        ))}
      </div>

      {/* Loading State - Only show if no messages yet */}
      {isLoading && messages.length === 0 && (
        <motion.div 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-center gap-3 mt-4"
        >
          <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
            <div className="w-4 h-4 bg-green-500 rounded-full animate-pulse"></div>
          </div>
          <div className="bg-gray-100 rounded-2xl px-4 py-3">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
              <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
            </div>
          </div>
        </motion.div>
      )}

      {/* Scroll anchor */}
      <div ref={messagesEndRef} />
    </div>
  )
}