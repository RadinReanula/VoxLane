import { PipecatClient } from "@pipecat-ai/client-js";
import { SmallWebRTCTransport } from "@pipecat-ai/small-webrtc-transport";

export type AudioGeneration = {
  id: number;
  stop: () => void;
};

export class OptionalVoiceAdapter {
  private stream?: MediaStream;
  private generation = 0;
  private activeAudio = new Set<HTMLAudioElement>();
  private client?: PipecatClient;

  async requestMicrophone(): Promise<MediaStream> {
    this.stream = await navigator.mediaDevices.getUserMedia({
      audio: {
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
      video: false,
    });
    return this.stream;
  }

  async connect(endpoint: string): Promise<boolean> {
    this.stream ??= await this.requestMicrophone();
    this.client = new PipecatClient({
      transport: new SmallWebRTCTransport({
        iceServers: [{ urls: "stun:stun.l.google.com:19302" }],
      }),
      enableMic: true,
      enableCam: false,
    });
    await this.client.connect({ webrtcUrl: endpoint });
    return true;
  }

  beginGeneration(): AudioGeneration {
    const id = ++this.generation;
    return { id, stop: () => this.interrupt() };
  }

  attachPlayout(audio: HTMLAudioElement, generation: number): boolean {
    if (generation !== this.generation) {
      audio.pause();
      audio.srcObject = null;
      return false;
    }
    this.activeAudio.add(audio);
    audio.addEventListener(
      "ended",
      () => this.activeAudio.delete(audio),
      { once: true },
    );
    return true;
  }

  isCurrent(generation: number): boolean {
    return generation === this.generation;
  }

  interrupt(): void {
    this.generation += 1;
    this.activeAudio.forEach((audio) => {
      audio.pause();
      audio.currentTime = 0;
      audio.srcObject = null;
    });
    this.activeAudio.clear();
  }

  disconnect(): void {
    this.interrupt();
    void this.client?.disconnect();
    this.client = undefined;
    this.stream?.getTracks().forEach((track) => track.stop());
    this.stream = undefined;
  }
}
