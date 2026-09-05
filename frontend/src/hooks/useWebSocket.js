import {useEffect,useRef} from 'react';
export function useWebSocket(chatId,onEvent){const ref=useRef(null);useEffect(()=>{if(!chatId)return;const base=location.protocol==='https:'?'wss':'ws';const ws=new WebSocket(`${base}://${location.host}/ws/${chatId}`);ref.current=ws;ws.onmessage=e=>{try{onEvent(JSON.parse(e.data))}catch{}};return()=>ws.close()},[chatId]);return ref}
