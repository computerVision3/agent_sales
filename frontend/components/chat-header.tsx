"use client"

import { motion } from "framer-motion"
import { Bot, MessageSquare } from "lucide-react"

export function ChatHeader() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="bg-gradient-to-r from-blue-600 to-green-600 text-white p-6 shadow-lg"
    >
      <div className="max-w-4xl mx-auto flex items-center gap-4">
        <motion.div
          initial={{ scale: 0 }}
          animate={{ scale: 1 }}
          transition={{ delay: 0.2, type: "spring", stiffness: 200 }}
          className="bg-white/20 p-3 rounded-full"
        >
          <Bot className="w-8 h-8" />
        </motion.div>
        <div>
          <motion.h1
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
            className="text-2xl font-bold"
          >
            ReAct Chat Interface
          </motion.h1>
          <motion.p
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
            className="text-blue-100 flex items-center gap-2"
          >
            <MessageSquare className="w-4 h-4" />
            Reasoning + Acting Agent
          </motion.p>
        </div>
      </div>
    </motion.div>
  )
}
