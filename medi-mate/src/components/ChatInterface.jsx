import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, ExternalLink, CheckCircle, Search, Brain } from 'lucide-react'
import { chatAPI } from '../services/api'

const ChatInterface = () => {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "안녕하세요! 💊\n복약지도 전문 AI입니다.\n\n💡 질문 예시:\n• '타이레놀과 애드빌 같이 먹어도 되나요?'\n• '임신 중 복용 가능한 감기약이 있나요?'\n• '낙센 하루에 몇 번 먹어야 하나요?'",
      sender: 'bot',
      timestamp: new Date(),
      sources: []
    }
  ])
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [loadingStage, setLoadingStage] = useState('')
  const [showSources, setShowSources] = useState({})
  const messagesEndRef = useRef(null)
  const inputRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // iOS 키보드 처리
  useEffect(() => {
    const handleResize = () => {
      setTimeout(() => scrollToBottom(), 100)
    }
    window.addEventListener('resize', handleResize)
    return () => window.removeEventListener('resize', handleResize)
  }, [])

  const getDateLabel = (date) => {
    const today = new Date()
    const messageDate = new Date(date)
    const diffTime = today - messageDate
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return '오늘'
    if (diffDays === 1) return '어제'
    return messageDate.toLocaleDateString('ko-KR')
  }

  const shouldShowDateLabel = (currentMsg, prevMsg) => {
    if (!prevMsg) return true
    const currentDate = new Date(currentMsg.timestamp).toDateString()
    const prevDate = new Date(prevMsg.timestamp).toDateString()
    return currentDate !== prevDate
  }

  const sendMessage = async () => {
    if (!input.trim()) return

    const userMessage = {
      id: Date.now(),
      text: input,
      sender: 'user',
      timestamp: new Date(),
      sources: []
    }

    setMessages(prev => [...prev, userMessage])
    const currentInput = input
    setInput('')
    setIsLoading(true)

    // iOS 키보드 숨기기
    if (inputRef.current) {
      inputRef.current.blur()
    }

    try {
      setLoadingStage('관련 문서를 찾는 중...')
      await new Promise(resolve => setTimeout(resolve, 500))

      setLoadingStage('답변 생성 중...')
      const { data } = await chatAPI.sendMessage(currentInput)

      const botMessage = {
        id: Date.now() + 1,
        text: data.response,
        sender: 'bot',
        timestamp: new Date(),
        sources: data.sources || [],
        processingTime: data.processing_time,
        modelUsed: data.model_used
      }

      setMessages(prev => [...prev, botMessage])
    } catch (error) {
      console.error('❌ API 요청 오류:', error)

      let errorMessage = "죄송합니다. 일시적인 오류가 발생했습니다. 🔧\n잠시 후 다시 시도해주세요."

      const errorBotMessage = {
        id: Date.now() + 1,
        text: errorMessage + '\n\n⚠️ 이 정보는 의료진 상담을 대체할 수 없습니다.',
        sender: 'bot',
        timestamp: new Date(),
        sources: []
      }
      setMessages(prev => [...prev, errorBotMessage])
    } finally {
      setIsLoading(false)
      setLoadingStage('')
    }
  }

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  const toggleSources = (messageId) => {
    setShowSources(prev => ({
      ...prev,
      [messageId]: !prev[messageId]
    }))
  }

  const openSourceLink = (url) => {
    if (url && url !== '') {
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <div className="h-screen bg-gray-50 flex flex-col max-w-md sm:max-w-lg md:max-w-2xl lg:max-w-4xl mx-auto border-x border-gray-200">
      {/* 헤더 */}
      <div className="bg-[#5b9bd5] px-4 py-3 text-white flex-shrink-0 shadow-lg">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 bg-white/20 rounded-full flex items-center justify-center">
            <Bot className="w-4 h-4" />
          </div>
          <div className="flex-1 min-w-0">
            <h1 className="font-bold text-lg">복약지도 AI</h1>
            <div className="flex items-center gap-1 text-xs text-blue-100">
              <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
              RAG 시스템 온라인
            </div>
          </div>
        </div>
        <div className="mt-2">
          <p className="text-xs text-blue-100 text-center bg-white/10 px-3 py-1 rounded-lg">
            ⚠️ 응급시 119, 정확한 진단은 의료진과 상담하세요
          </p>
        </div>
      </div>

      {/* 채팅 영역 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white">
        {messages.map((message, index) => {
          const prevMessage = index > 0 ? messages[index - 1] : null
          const showDate = shouldShowDateLabel(message, prevMessage)

          return (
            <div key={message.id}>
              {/* 날짜 라벨 */}
              {showDate && (
                <div className="text-center my-3">
                  <span className="bg-gray-100 text-gray-600 text-xs px-3 py-1 rounded-full">
                    {getDateLabel(message.timestamp)}
                  </span>
                </div>
              )}

              {/* 메시지 - 카카오톡 스타일 */}
              <div className={`flex items-start gap-2 ${message.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                {/* 아바타 */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${message.sender === 'user' ? 'bg-[#5b9bd5]' : 'bg-green-500'
                  } text-white`}>
                  {message.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
                </div>

                {/* 메시지 박스와 시간 */}
                <div className={`flex items-end gap-1 max-w-[70%] ${message.sender === 'user' ? 'flex-row-reverse' : ''}`}>
                  {/* 메시지 박스 */}
                  <div className={`px-3 py-2 rounded-2xl ${message.sender === 'user'
                      ? 'bg-[#5b9bd5] text-white rounded-br-md'
                      : 'bg-gray-100 text-gray-800 rounded-bl-md'
                    }`}>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">
                      {message.text}
                    </p>
                  </div>

                  {/* 시간 */}
                  <div className="text-xs text-gray-400 flex-shrink-0 pb-1">
                    {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                  </div>
                </div>
              </div>

              {/* 출처 정보 */}
              {message.sender === 'bot' && message.sources && message.sources.length > 0 && (
                <div className="ml-10 mt-2">
                  <button
                    onClick={() => toggleSources(message.id)}
                    className="flex items-center gap-1 text-xs text-[#5b9bd5] hover:text-blue-700"
                  >
                    <CheckCircle size={10} />
                    출처 {message.sources.length}개 보기 {showSources[message.id] ? '▼' : '▶'}
                  </button>

                  {showSources[message.id] && (
                    <div className="mt-2 p-2 bg-blue-50 rounded-lg border-l-4 border-[#5b9bd5]">
                      <h4 className="font-semibold mb-2 text-xs text-gray-700">참고 자료:</h4>
                      <div className="text-xs space-y-2">
                        {message.sources.map((source, idx) => (
                          <div key={idx} className="flex items-start gap-2 p-2 bg-white rounded border">
                            <span className="bg-[#5b9bd5] text-white px-1 py-0.5 rounded text-xs font-mono">
                              {source.rank}
                            </span>
                            <div className="flex-1 min-w-0">
                              <button
                                onClick={() => openSourceLink(source.url)}
                                className="font-medium text-gray-800 hover:text-[#5b9bd5] flex items-center gap-1 text-left w-full"
                              >
                                <span className="truncate">{source.source}</span>
                                <ExternalLink size={8} />
                              </button>
                              <div className="text-gray-600 mt-1">카테고리: {source.category}</div>
                              <div className="text-gray-500">유사도: {(source.similarity * 100).toFixed(1)}%</div>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              )}
            </div>
          )
        })}

        {/* 로딩 인디케이터 */}
        {isLoading && (
          <div className="flex items-start gap-2">
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center text-white">
              <Bot size={14} />
            </div>
            <div className="flex items-end gap-1 max-w-[70%]">
              <div className="bg-gray-100 rounded-2xl rounded-bl-md px-3 py-2">
                <div className="flex items-center space-x-2">
                  {loadingStage === '관련 문서를 찾는 중...' && (
                    <Search size={10} className="text-[#5b9bd5] animate-pulse" />
                  )}
                  {loadingStage === '답변 생성 중...' && (
                    <Brain size={10} className="text-purple-500 animate-pulse" />
                  )}
                  <span className="text-xs text-gray-600">{loadingStage || 'RAG 검색 중...'}</span>
                  <div className="flex space-x-1">
                    <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce"></div>
                    <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                    <div className="w-1 h-1 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  </div>
                </div>
              </div>
              <div className="text-xs text-gray-400 flex-shrink-0 pb-1">
                {new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* 입력 영역 */}
      <div className="bg-white border-t border-gray-200 p-4 flex-shrink-0">
        <div className="flex gap-2 items-center bg-gray-100 rounded-3xl px-4 py-2">
          <input
            ref={inputRef}
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="타이레놀과 애드빌 같이 먹어도 되나요?"
            className="flex-1 bg-transparent border-0 focus:outline-none text-sm"
            disabled={isLoading}
            style={{
              fontSize: '16px', // iOS 확대 방지
              WebkitAppearance: 'none'
            }}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="bg-[#5b9bd5] text-white p-2 rounded-full hover:bg-blue-600 disabled:opacity-50 transition-all active:scale-95"
            style={{ WebkitTapHighlightColor: 'transparent' }}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface