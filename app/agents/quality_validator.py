# app/agents/quality_validator.py - faster-whisper 기반 음성 품질 검증 시스템

from faster_whisper import WhisperModel
import os
import difflib
from typing import Dict, Any, Optional, List
import logging
import numpy as np
from pathlib import Path

# librosa import 처리 (선택적)
try:
    import librosa
    LIBROSA_AVAILABLE = True
except ImportError:
    LIBROSA_AVAILABLE = False
    print("⚠️ librosa를 사용할 수 없습니다. 기본 오디오 분석만 수행됩니다.")

logger = logging.getLogger(__name__)

class AudioQualityValidator:
    """
    faster-whisper를 활용한 TTS 음성 품질 검증 시스템
    """

    def __init__(self, whisper_model: str = "base"):
        print(f"🔍 AudioQualityValidator 초기화:")
        print(f"  - Whisper 모델(faster-whisper): {whisper_model}")
        print(f"  - Librosa 사용 가능: {LIBROSA_AVAILABLE}")

        try:
            self.whisper_model = WhisperModel(
                whisper_model,
                device="cpu",  # GPU 사용 시 "cuda"
                compute_type="int8"
            )
            self.available = True
            print("✅ AudioQualityValidator: faster-whisper 모델 로드 완료")
        except Exception as e:
            logger.error(f"faster-whisper 모델 로드 실패: {e}")
            self.whisper_model = None
            self.available = False
            print("❌ AudioQualityValidator: 모델 로드 실패 - 품질 검증 비활성화")

    def validate_audio_quality(self, audio_file_path: str, original_text: str, min_similarity: float = 0.8) -> Dict[str, Any]:
        if not self.available:
            return {
                "available": False,
                "message": "Whisper 모델을 사용할 수 없습니다",
                "overall_score": 0.0,
                "passed": False
            }

        if not os.path.exists(audio_file_path):
            return {
                "available": True,
                "error": f"음성 파일을 찾을 수 없습니다: {audio_file_path}",
                "overall_score": 0.0,
                "passed": False
            }

        print(f"🔍 음성 품질 검증 시작: {Path(audio_file_path).name}")
        try:
            # 1. STT
            transcription_result = self._transcribe_audio(audio_file_path)

            # 2. 텍스트 유사도
            similarity_result = self._calculate_text_similarity(
                original_text,
                transcription_result["text"]
            )

            # 3. 오디오 품질 분석
            audio_quality_result = self._analyze_audio_quality(audio_file_path)

            # 4. 종합 점수
            overall_score = self._calculate_overall_score(
                similarity_result,
                audio_quality_result,
                transcription_result
            )

            return {
                "available": True,
                "audio_file": audio_file_path,
                "original_text": original_text,
                "transcribed_text": transcription_result["text"],
                "transcription_confidence": transcription_result.get("confidence", 0.0),
                "text_similarity": similarity_result,
                "audio_quality": audio_quality_result,
                "overall_score": overall_score,
                "passed": overall_score >= min_similarity,
                "min_similarity": min_similarity,
                "recommendations": self._generate_recommendations(
                    overall_score, similarity_result, audio_quality_result
                )
            }

        except Exception as e:
            logger.error(f"품질 검증 중 오류: {e}")
            return {
                "available": True,
                "error": str(e),
                "overall_score": 0.0,
                "passed": False
            }

    def _transcribe_audio(self, audio_file_path: str) -> Dict[str, Any]:
        print("  🎤 faster-whisper STT 실행 중...")
        try:
            segments, info = self.whisper_model.transcribe(audio_file_path, language="ko", beam_size=5)
            texts = []
            confidences = []

            for segment in segments:
                texts.append(segment.text.strip())
                if segment.avg_logprob is not None:
                    confidences.append(np.exp(min(0, segment.avg_logprob)))

            transcript_text = " ".join(texts)

            return {
                "text": transcript_text.strip(),
                "language": info.language,
                "segments": texts,
                "confidence": float(np.mean(confidences)) if confidences else 0.0
            }
        except Exception as e:
            logger.error(f"STT 실패: {e}")
            return {
                "text": "",
                "error": str(e),
                "confidence": 0.0
            }

    def _calculate_text_similarity(self, original: str, transcribed: str) -> Dict[str, float]:
        print("  📊 텍스트 유사도 계산 중...")
        import re
        original_clean = re.sub(r'\s+', ' ', original.strip())
        transcribed_clean = re.sub(r'\s+', ' ', transcribed.strip())

        char_similarity = difflib.SequenceMatcher(None, original_clean, transcribed_clean).ratio()
        word_similarity = difflib.SequenceMatcher(None, original_clean.split(), transcribed_clean.split()).ratio()
        length_similarity = min(len(original_clean), len(transcribed_clean)) / max(len(original_clean), len(transcribed_clean)) if max(len(original_clean), len(transcribed_clean)) else 0

        return {
            "character_similarity": char_similarity,
            "word_similarity": word_similarity,
            "length_similarity": length_similarity,
            "average_similarity": (char_similarity + word_similarity + length_similarity) / 3
        }

    def _analyze_audio_quality(self, audio_file_path: str) -> Dict[str, Any]:
        print("  🔊 오디오 품질 분석 중...")
        if not LIBROSA_AVAILABLE:
            return {
                "librosa_available": False,
                "quality_score": 0.5,
                "message": "librosa 없음"
            }
        try:
            y, sr = librosa.load(audio_file_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            rms = librosa.feature.rms(y=y)[0]
            avg_rms = float(np.mean(rms))
            zcr = librosa.feature.zero_crossing_rate(y)[0]
            avg_zcr = float(np.mean(zcr))
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)[0]
            avg_spectral_centroid = float(np.mean(spectral_centroids))
            silence_ratio = np.sum(np.abs(y) < 0.01) / len(y)

            quality_score = self._calculate_audio_quality_score(
                avg_rms, avg_zcr, avg_spectral_centroid, silence_ratio, duration
            )

            return {
                "librosa_available": True,
                "duration": duration,
                "sample_rate": sr,
                "avg_rms": avg_rms,
                "avg_zero_crossing_rate": avg_zcr,
                "avg_spectral_centroid": avg_spectral_centroid,
                "silence_ratio": silence_ratio,
                "quality_score": quality_score
            }

        except Exception as e:
            logger.error(f"오디오 분석 실패: {e}")
            return {
                "librosa_available": True,
                "error": str(e),
                "quality_score": 0.5
            }

    def _calculate_overall_score(self, similarity_result: Dict, audio_quality_result: Dict, transcription_result: Dict) -> float:
        weights = {
            "text_similarity": 0.6,
            "audio_quality": 0.3,
            "transcription_confidence": 0.1
        }
        return round(
            similarity_result.get("average_similarity", 0) * weights["text_similarity"] +
            audio_quality_result.get("quality_score", 0.5) * weights["audio_quality"] +
            transcription_result.get("confidence", 0.0) * weights["transcription_confidence"],
            3
        )

    def _calculate_audio_quality_score(self, avg_rms: float, avg_zcr: float, avg_spectral_centroid: float, silence_ratio: float, duration: float) -> float:
        score = 0.0
        if 0.01 <= avg_rms <= 0.3:
            score += 0.3
        if silence_ratio < 0.1:
            score += 0.2
        elif silence_ratio < 0.2:
            score += 0.1
        if 0.05 <= avg_zcr <= 0.2:
            score += 0.2
        if 1000 <= avg_spectral_centroid <= 4000:
            score += 0.2
        if 1.0 <= duration <= 30.0:
            score += 0.1
        return min(1.0, score)

    def _generate_recommendations(self, overall_score: float, similarity_result: Dict, audio_quality_result: Dict) -> List[str]:
        recommendations = []
        if overall_score < 0.6:
            recommendations.append("전반적인 품질이 낮습니다. 재생성을 권장합니다.")
        if similarity_result.get("character_similarity", 0) < 0.7:
            recommendations.append("텍스트 유사도가 낮습니다. 발음이 부정확할 수 있습니다.")
        if audio_quality_result.get("avg_rms", 0) < 0.01:
            recommendations.append("음량이 너무 낮습니다.")
        elif audio_quality_result.get("avg_rms", 0) > 0.3:
            recommendations.append("음량이 너무 큽니다.")
        if audio_quality_result.get("silence_ratio", 0) > 0.2:
            recommendations.append("무음 구간이 너무 많습니다.")
        if not recommendations:
            recommendations.append("품질이 양호합니다.")
        return recommendations