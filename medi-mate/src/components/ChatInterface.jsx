import { useState, useRef, useEffect } from 'react'
import { Send, Bot, User, ExternalLink, Copy, RotateCcw, CheckCircle, Search, Brain } from 'lucide-react'
import { chatAPI } from './api'

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
  const [copiedMessageId, setCopiedMessageId] = useState(null)
  const messagesEndRef = useRef(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  // 날짜 라벨 생성 함수
  const getDateLabel = (date) => {
    const today = new Date()
    const messageDate = new Date(date)

    const diffTime = today - messageDate
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

    if (diffDays === 0) return '오늘'
    if (diffDays === 1) return '어제'
    return messageDate.toLocaleDateString('ko-KR')
  }

  // 날짜가 바뀐 메시지인지 확인
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

    try {
      console.log('📤 RAG 요청 전송:', currentInput)

      // 🔄 단계별 로딩 상태 표시
      setLoadingStage('관련 문서를 찾는 중...')
      await new Promise(resolve => setTimeout(resolve, 500)) // 시뮬레이션

      setLoadingStage('답변 생성 중...')

      const { data } = await chatAPI.sendMessage(currentInput)

      console.log('📥 RAG 응답 수신:', data)

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

      if (error.response?.status === 500) {
        errorMessage = "🔧 서버 내부 오류가 발생했습니다.\nRAG 시스템을 확인해주세요."
      } else if (error.message?.includes('timeout')) {
        errorMessage = "⏱️ 요청 시간이 초과되었습니다.\n서버가 응답하지 않고 있습니다."
      }

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

  // 💬 메시지 복사 기능
  const copyMessage = async (text, messageId) => {
    try {
      await navigator.clipboard.writeText(text)
      setCopiedMessageId(messageId)
      setTimeout(() => setCopiedMessageId(null), 2000)
    } catch (err) {
      console.error('복사 실패:', err)
    }
  }

  // 🔄 다시 물어보기 기능
  const askAgain = (text) => {
    setInput(text)
  }

  // 🔗 출처 링크 열기
  const openSourceLink = (url) => {
    if (url && url !== '') {
      window.open(url, '_blank', 'noopener,noreferrer')
    }
  }

  return (
    <div className="h-screen bg-gray-50 flex flex-col max-w-md sm:max-w-lg md:max-w-2xl lg:max-w-4xl mx-auto border-x border-gray-200">
      {/* 헤더 */}
      <div className="bg-[#5b9bd5] px-4 py-3 text-white flex-shrink-0 shadow-lg rounded-b-2xl">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 bg-white/20 rounded-full flex items-center justify-center">
            <Bot className="w-5 h-5" />
          </div>
          <div className="flex-1">
            <h1 className="font-bold text-lg">복약지도 AI</h1>
            <div className="flex items-center gap-1 text-xs text-blue-100">
              <div className="w-1.5 h-1.5 bg-green-400 rounded-full animate-pulse"></div>
              RAG 시스템 온라인
            </div>
          </div>
          {/* 안전 고지 - 헤더 하단 */}
          <div className="mt-2 text-center">
            <p className="text-xs text-blue-100 bg-white/10 px-3 py-1 rounded-full border border-white/20">
              ⚠️ 응급시 119, 정확한 진단은 의료진과 상담하세요
            </p>
          </div>
        </div>
      </div>

      {/* 채팅 영역 */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-white">
        {messages.map((message, index) => {
          const prevMessage = index > 0 ? messages[index - 1] : null
          const showDate = shouldShowDateLabel(message, prevMessage)

          return (
            <div key={message.id}>
              {/* 📅 날짜 라벨 */}
              {showDate && (
                <div className="text-center my-4">
                  <span className="bg-gray-100 text-gray-600 text-xs px-3 py-1 rounded-full shadow-sm">
                    {getDateLabel(message.timestamp)}
                  </span>
                </div>
              )}

              {/* 메시지 */}
              <div
                className={`flex gap-3 animate-in slide-in-from-bottom-2 duration-300 group ${message.sender === 'user' ? 'flex-row-reverse' : ''
                  }`}
                style={{ animationDelay: `${index * 50}ms` }}
              >
                {/* 아바타 */}
                <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${message.sender === 'user'
                  ? 'bg-[#5b9bd5] text-white'
                  : 'bg-green-500 text-white'
                  }`}>
                  {message.sender === 'user' ? <User size={14} /> : <Bot size={14} />}
                </div>

                {/* 메시지 */}
                <div className={`max-w-[75%] relative ${message.sender === 'user' ? 'items-end' : 'items-start'}`}>
                  <div className={`px-4 py-3 rounded-2xl shadow-md transition-all relative ${message.sender === 'user'
                    ? 'bg-[#5b9bd5] text-white rounded-br-md'
                    : 'bg-gray-100 text-gray-800 rounded-bl-md'
                    }`}>
                    <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.text}</p>

                    {/* 💬 메시지 인터랙션 버튼 (호버시 표시) */}
                    <div className={`absolute top-2 ${message.sender === 'user' ? '-left-12' : '-right-12'} opacity-0 group-hover:opacity-100 transition-opacity duration-200`}>
                      <div className="flex flex-col space-y-1">
                        <button
                          onClick={() => copyMessage(message.text, message.id)}
                          className="p-1.5 bg-white shadow-lg rounded-full hover:bg-gray-50 transition-colors"
                          title="복사"
                        >
                          {copiedMessageId === message.id ? (
                            <CheckCircle size={12} className="text-green-600" />
                          ) : (
                            <Copy size={12} className="text-gray-600" />
                          )}
                        </button>
                        {message.sender === 'user' && (
                          <button
                            onClick={() => askAgain(message.text)}
                            className="p-1.5 bg-white shadow-lg rounded-full hover:bg-gray-50 transition-colors"
                            title="다시 물어보기"
                          >
                            <RotateCcw size={12} className="text-gray-600" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* 📚 출처 정보 */}
                  {message.sender === 'bot' && message.sources && message.sources.length > 0 && (
                    <div className="mt-2">
                      <button
                        onClick={() => toggleSources(message.id)}
                        className="flex items-center gap-1 text-xs text-[#5b9bd5] hover:text-blue-700 transition-colors"
                      >
                        <CheckCircle size={12} />
                        출처 {message.sources.length}개 보기
                        {showSources[message.id] ? ' ▼' : ' ▶'}
                      </button>

                      {showSources[message.id] && (
                        <div className="mt-2 p-3 bg-blue-50 rounded-lg border-l-4 border-[#5b9bd5] transition-all duration-300">
                          <h4 className="font-semibold mb-2 text-xs text-gray-700">참고 자료:</h4>
                          <div className="text-xs space-y-2">
                            {message.sources.map((source, idx) => (
                              <div key={idx} className="flex items-start gap-2 p-2 bg-white rounded border">
                                <span className="bg-[#5b9bd5] text-white px-1.5 py-0.5 rounded text-xs font-mono">
                                  {source.rank}
                                </span>
                                <div className="flex-1">
                                  <button
                                    onClick={() => openSourceLink(source.url)}
                                    className="font-medium text-gray-800 hover:text-[#5b9bd5] transition-colors flex items-center gap-1 group text-left"
                                  >
                                    {source.source}
                                    <ExternalLink size={10} className="opacity-0 group-hover:opacity-100 transition-opacity" />
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

                  {/* 메타데이터 */}
                  <div className="text-xs mt-1 px-1 flex items-center gap-2">
                    <span>{message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    {message.modelUsed && message.modelUsed !== 'fallback' && (
                      <span className="text-green-600">• RAG</span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}

        {/* 🔄 강화된 로딩 인디케이터 */}
        {isLoading && (
          <div className="flex gap-3 animate-in slide-in-from-bottom-2">
            <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
              <Bot size={14} className="text-white" />
            </div>
            <div className="bg-gray-100 rounded-2xl rounded-bl-md px-4 py-3 shadow-md">
              <div className="flex items-center space-x-2">
                {loadingStage === '관련 문서를 찾는 중...' && (
                  <Search size={12} className="text-[#5b9bd5] animate-pulse" />
                )}
                {loadingStage === '답변 생성 중...' && (
                  <Brain size={12} className="text-purple-500 animate-pulse" />
                )}
                <span className="text-xs text-gray-600">{loadingStage || 'RAG 검색 중...'}</span>
                <div className="flex space-x-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* 입력 영역 */}
      <div className="bg-white border-t border-gray-200 p-4 flex-shrink-0">
        <div className="flex gap-2 items-center bg-gray-100 rounded-3xl px-3 py-2 shadow-inner">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder={`예: "타이레놀과 애드빌 같이 먹어도 되나요?", "임신 중 감기약 복용법"`}
            className="flex-1 bg-transparent border-0 focus:outline-none text-sm px-2"
            disabled={isLoading}
          />
          <button
            onClick={sendMessage}
            disabled={!input.trim() || isLoading}
            className="bg-[#5b9bd5] text-white p-2 rounded-full hover:bg-blue-600 disabled:opacity-50 transition-all active:scale-95 shadow-md"
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  )
}

export default ChatInterface