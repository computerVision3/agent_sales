"use client"

import { useState } from "react"
import { motion, AnimatePresence } from "framer-motion"
import { ChevronRight, User, Bot, Wrench } from "lucide-react"
import { cn } from "@/lib/utils"

interface ChatMessageProps {
  sender: "human" | "ai" | "tool"
  content: string
  index: number
}

export function ChatMessage({ sender, content, index }: ChatMessageProps) {
  const [isThinkingExpanded, setIsThinkingExpanded] = useState(false)
  const [isToolExpanded, setIsToolExpanded] = useState(false)
  const [expandedCSV, setExpandedCSV] = useState<{ [path: string]: boolean }>({})

  const toggleCSV = (path: string) => {
    setExpandedCSV(prev => ({ ...prev, [path]: !prev[path] }))
  }

  const parseThinking = (text: string) => {
    const thinkingRegex = /<Thinking>(.*?)<\/Thinking>/gs
    const parts = []
    let lastIndex = 0
    let match

    while ((match = thinkingRegex.exec(text)) !== null) {
      if (match.index > lastIndex) {
        parts.push({ type: "text", content: text.slice(lastIndex, match.index) })
      }
      parts.push({ type: "thinking", content: match[1].trim() })
      lastIndex = match.index + match[0].length
    }

    if (lastIndex < text.length) {
      parts.push({ type: "text", content: text.slice(lastIndex) })
    }

    return parts.length > 0 ? parts : [{ type: "text", content: text }]
  }

  const cleanToolOutput = (content: string) => {
    const lines = content.split("\n")
    const seen = new Set()
    const uniqueLines = []

    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed && !seen.has(trimmed)) {
        seen.add(trimmed)
        uniqueLines.push(line)
      } else if (!trimmed) {
        uniqueLines.push(line)
      }
    }

    return uniqueLines.join("\n")
  }

  const getToolSummary = (content: string) => {
    const cleaned = cleanToolOutput(content)
    const lines = cleaned.split("\n").filter(line => line.trim())
    if (lines.length === 0) return "Tool output"

    const firstLine = lines[0].trim()
    if (firstLine.length > 60) {
      return firstLine.substring(0, 60) + "..."
    }
    return firstLine
  }

  const getMessageStyles = () => {
    switch (sender) {
      case "human":
        return {
          container: "justify-end",
          bubble: "bg-blue-500 text-white max-w-[80%] shadow-lg",
          alignment: "ml-auto",
          icon: User,
        }
      case "ai":
        return {
          container: "justify-start",
          bubble: "bg-green-50 text-green-900 border border-green-200 max-w-[85%] shadow-md",
          alignment: "mr-auto",
          icon: Bot,
        }
      case "tool":
        return {
          container: "justify-start",
          bubble: "bg-gray-50 text-gray-800 border border-gray-200 max-w-[75%] shadow-sm",
          alignment: "mr-auto",
          icon: Wrench,
        }
      default:
        return {
          container: "justify-start",
          bubble: "bg-gray-100 text-gray-800 max-w-[80%]",
          alignment: "mr-auto",
          icon: Bot,
        }
    }
  }

  const getFileName = (path: string) => path.split("/").pop()

  const renderToolOutput = (text: string) => {
  let parsed: any = null
  try {
    // Replace single quotes with double quotes to handle raw Python-style dicts
    parsed = JSON.parse(text.replace(/'/g, '"'))
  } catch {
    parsed = null
  }

  // If parsed JSON contains a CSV path
  if (parsed && parsed.path && parsed.path.endsWith(".csv")) {
    const fileName = getFileName(parsed.path)
    const isExpanded = expandedCSV[parsed.path] || false

    return (
      <div className="space-y-2">
        <motion.button
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          onClick={() => toggleCSV(parsed.path)}
          className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-800 transition-colors p-1 rounded hover:bg-gray-100 w-full text-left"
        >
          <motion.div animate={{ rotate: isExpanded ? 90 : 0 }} transition={{ duration: 0.2 }}>
            <ChevronRight className="w-4 h-4" />
          </motion.div>
          {/* Always show the JSON message, fallback to "Tool Output" */}
          <span className="font-medium">{parsed.message || "Tool Output"}</span>
          <span className="text-gray-600 truncate ml-2">{fileName}</span>
        </motion.button>

        <AnimatePresence>
          {isExpanded && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
              transition={{ duration: 0.3 }}
              className="overflow-hidden mt-2"
            >
              <div className="flex flex-col gap-2 p-3 bg-gray-50 rounded-lg border border-gray-200 text-sm">
                {parsed.message && <div className="text-gray-700">{parsed.message}</div>}
                <div className="text-gray-500 text-xs">Path:</div>
                <div className="text-gray-800 break-all">{parsed.path}</div>
                <a
                  href={`http://192.168.1.152:8000/download?path=${encodeURIComponent(parsed.path)}`}
                  className="text-blue-600 hover:underline font-medium mt-1 block"
                  download
                >
                  ⬇️ Download {fileName}
                </a>
                {parsed.success_count !== undefined && (
                  <div className="text-xs text-gray-600">✅ Success: {parsed.success_count}</div>
                )}
                {parsed.failed_count !== undefined && (
                  <div className="text-xs text-gray-600">❌ Failed: {parsed.failed_count}</div>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    )
  }

  // Handle plain CSV paths in text
  const csvRegex = /\/[^\s]+\.csv/g
  const cleaned = cleanToolOutput(text)
  const matches = cleaned.match(csvRegex)
  if (matches) {
    return matches.map((path, idx) => {
      const fileName = getFileName(path)
      const isExpanded = expandedCSV[path] || false
      return (
        <div key={idx} className="space-y-1">
          <motion.button
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            onClick={() => toggleCSV(path)}
            className="flex items-center gap-2 text-sm text-gray-700 hover:text-gray-800 transition-colors p-1 rounded hover:bg-gray-100 w-full text-left"
          >
            <motion.div animate={{ rotate: isExpanded ? 90 : 0 }} transition={{ duration: 0.2 }}>
              <ChevronRight className="w-4 h-4" />
            </motion.div>
            <span className="font-medium">Tool Output</span>
            <span className="text-gray-600 truncate ml-2">{fileName}</span>
          </motion.button>

          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                transition={{ duration: 0.3 }}
                className="overflow-hidden mt-2"
              >
                <div className="flex flex-col gap-2 p-3 bg-gray-50 rounded-lg border border-gray-200 text-sm">
                  <div className="text-gray-500 text-xs">Path:</div>
                  <div className="text-gray-800 break-all">{path}</div>
                  <a
                    href={`sandbox:${path}`}
                    className="text-blue-600 hover:underline font-medium mt-1 block"
                    download
                  >
                    ⬇️ Download {fileName}
                  </a>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )
    })
  }

  return <div>{cleaned}</div>
}


  const styles = getMessageStyles()
  const parsedContent = sender === "ai" ? parseThinking(content) : [{ type: "text", content }]
  const IconComponent = styles.icon

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{
        duration: 0.4,
        delay: index * 0.1,
        type: "spring",
        stiffness: 200,
        damping: 20,
      }}
      className={cn("flex w-full mb-6", styles.container)}
    >
      <div className="flex items-start gap-3 max-w-full">
        {sender !== "human" && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: index * 0.1 + 0.2 }}
            className={cn(
              "flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center",
              sender === "ai" ? "bg-green-100 text-green-600" : "bg-gray-100 text-gray-600",
            )}
          >
            <IconComponent className="w-4 h-4" />
          </motion.div>
        )}

        <div className={cn("rounded-xl px-4 py-3 relative", styles.bubble, styles.alignment)}>
          {sender === "tool" ? (
            <div>{renderToolOutput(content)}</div>
          ) : (
            parsedContent.map((part, partIndex) => (
              <div key={partIndex}>
                {part.type === "text" && <div className="whitespace-pre-wrap leading-relaxed">{part.content}</div>}
                {part.type === "thinking" && (
                  <div className="mt-3 border-t border-green-300 pt-3">
                    <motion.button
                      whileHover={{ scale: 1.02 }}
                      whileTap={{ scale: 0.98 }}
                      onClick={() => setIsThinkingExpanded(!isThinkingExpanded)}
                      className="flex items-center gap-2 text-sm text-green-700 hover:text-green-800 transition-colors p-1 rounded hover:bg-green-100"
                    >
                      <motion.div animate={{ rotate: isThinkingExpanded ? 90 : 0 }} transition={{ duration: 0.2 }}>
                        <ChevronRight className="w-4 h-4" />
                      </motion.div>
                      <span className="italic font-medium">Reasoning...</span>
                    </motion.button>
                    <AnimatePresence>
                      {isThinkingExpanded && (
                        <motion.div
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: "auto" }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.3 }}
                          className="overflow-hidden"
                        >
                          <div className="mt-3 p-4 bg-green-50 rounded-lg border border-green-200 text-sm italic text-green-800 leading-relaxed">
                            <div className="whitespace-pre-wrap">{part.content}</div>
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>
                  </div>
                )}
              </div>
            ))
          )}
        </div>

        {sender === "human" && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            transition={{ delay: index * 0.1 + 0.2 }}
            className="flex-shrink-0 w-8 h-8 rounded-full bg-blue-100 text-blue-600 flex items-center justify-center"
          >
            <User className="w-4 h-4" />
          </motion.div>
        )}
      </div>
    </motion.div>
  )
}
