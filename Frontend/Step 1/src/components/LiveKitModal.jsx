import { useState, useCallback } from "react";
import { LiveKitRoom, RoomAudioRenderer } from "@livekit/components-react";
import "@livekit/components-styles";
import SimpleVoiceAssistant from "./SimpleVoiceAssistant";

const LiveKitModal = ({ setShowSupport }) => {
  

  return (
    <div className="modal-overlay">
      <div className="modal-content">
        <div className="support-room">
          
            <LiveKitRoom
              serverUrl={import.meta.env.VITE_LIVEKIT_URL}
              token="[TOKEN_HERE]" // Replace with a valid token
              connect={true}
              video={false}
              audio={true}
              onDisconnected={() => {
                setShowSupport(false);
                setIsSubmittingName(true);
              }}
            >
              <RoomAudioRenderer />
              <SimpleVoiceAssistant />
            </LiveKitRoom>
          
        </div>
      </div>
    </div>
  );
};

export default LiveKitModal;
