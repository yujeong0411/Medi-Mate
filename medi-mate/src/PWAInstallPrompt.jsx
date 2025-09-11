// src/components/PWAInstallPrompt.jsx
import { useState, useEffect } from 'react'
import { Download, X } from 'lucide-react'

const PWAInstallPrompt = () => {
  const [deferredPrompt, setDeferredPrompt] = useState(null)
  const [showInstallPrompt, setShowInstallPrompt] = useState(false)

  useEffect(() => {
    const handler = (e) => {
      // 브라우저의 기본 설치 프롬프트 방지
      e.preventDefault()
      setDeferredPrompt(e)
      setShowInstallPrompt(true)
    }

    window.addEventListener('beforeinstallprompt', handler)

    return () => {
      window.removeEventListener('beforeinstallprompt', handler)
    }
  }, [])

  const handleInstall = async () => {
    if (!deferredPrompt) return

    deferredPrompt.prompt()
    const { outcome } = await deferredPrompt.userChoice

    if (outcome === 'accepted') {
      console.log('PWA 설치됨')
    }

    setDeferredPrompt(null)
    setShowInstallPrompt(false)
  }

  const handleDismiss = () => {
    setShowInstallPrompt(false)
    // 24시간 후 다시 표시
    localStorage.setItem('pwa-dismissed', Date.now())
  }

  // 이미 설치된 경우나 24시간 내 dismiss한 경우 숨김
  useEffect(() => {
    const dismissed = Number(localStorage.getItem('pwa-dismissed'))
    if (dismissed && Date.now() - dismissed < 24 * 60 * 60 * 1000) {
      setShowInstallPrompt(false)
    }

    // 이미 설치된 경우 확인
    if (
      (window.matchMedia('(display-mode: standalone)').matches) ||
      window.navigator.standalone === true
    ) {
      setShowInstallPrompt(false)
    }
  }, [])

  if (!showInstallPrompt) return null

  return (
    <div className="fixed bottom-20 left-4 right-4 bg-blue-600 text-white p-4 rounded-2xl shadow-lg z-50 animate-in slide-in-from-bottom-4">
      <div className="flex items-start gap-3">
        <div className="bg-white/20 p-2 rounded-lg">
          <Download className="w-5 h-5" />
        </div>
        <div className="flex-1">
          <h3 className="font-bold text-sm">앱으로 설치하기</h3>
          <p className="text-xs text-blue-100 mt-1">
            홈화면에 추가하여 더 빠르게 사용하세요
          </p>
        </div>
        <button
          onClick={handleDismiss}
          className="p-1 hover:bg-white/20 rounded-lg transition-colors"
        >
          <X className="w-4 h-4" />
        </button>
      </div>
      <div className="flex gap-2 mt-3">
        <button
          onClick={handleDismiss}
          className="flex-1 py-2 px-4 bg-white/20 rounded-lg text-sm font-medium hover:bg-white/30 transition-colors"
        >
          나중에
        </button>
        <button
          onClick={handleInstall}
          className="flex-1 py-2 px-4 bg-white text-blue-600 rounded-lg text-sm font-medium hover:bg-blue-50 transition-colors"
        >
          설치하기
        </button>
      </div>
    </div>
  )
}

export default PWAInstallPrompt