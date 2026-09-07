
import { useState } from 'react';
const seed = [
  {id:1, from:'other', text:'Привет! Добро пожаловать в Fenix Messenger.', time:'18:25'},
  {id:2, from:'other', text:'Здесь уже есть группы, реакции, поиск и real-time WebSocket.', time:'18:26'},
  {id:3, from:'me', text:'Отлично. Делаем полноценный мессенджер.', time:'18:28', seen:true},
  {id:4, from:'other', text:'Следующий шаг — подключить реальную БД и аккаунты.', time:'18:31'}
];
export default function ChatView({chat, onBack}) {
  const [messages,setMessages]=useState(seed);
  const [text,setText]=useState('');
  const send=()=>{const v=text.trim(); if(!v)return; setMessages(m=>[...m,{id:Date.now(),from:'me',text:v,time:new Date().toLocaleTimeString('ru-RU',{hour:'2-digit',minute:'2-digit'}),seen:true}]);setText('')};
  return <section className="chat-view">
    <header className="chat-header">
      <button className="mobile-back" onClick={onBack}>‹</button><div className="avatar">F</div>
      <div><b>{chat?.title || 'Чат'}</b><small>в сети · WebSocket</small></div>
      <div className="header-actions"><button>⌕</button><button>☎</button><button>⋮</button></div>
    </header>
    <div className="pinned">📌 <b>Закреплённое сообщение</b><span>Новый релиз Fenix v14</span></div>
    <div className="message-area">{messages.map(m=><div className={`message ${m.from}`} key={m.id}><div className="bubble">{m.text}<footer>{m.time}{m.seen?' ✓✓':''}</footer></div></div>)}</div>
    <div className="composer"><button>＋</button><input value={text} onChange={e=>setText(e.target.value)} onKeyDown={e=>e.key==='Enter'&&send()} placeholder="Сообщение" /><button>☺</button><button onClick={send}>➤</button></div>
  </section>
}
