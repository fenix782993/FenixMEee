
export default function ChatList({ chats, active, onSelect }) {
  return <div className="chat-list">
    <button className="archive-row" onClick={() => onSelect(1)}>
      <span className="archive-icon">▣</span><span><b>Архив</b><small>Скрытые чаты и каналы</small></span>
    </button>
    {chats.map(chat => <button className={`chat-row ${active === chat.id ? 'selected' : ''}`} key={chat.id} onClick={() => onSelect(chat.id)}>
      <span className="avatar">{chat.avatar}</span>
      <span className="chat-copy"><span><b>{chat.title}</b><time>{chat.time}</time></span><span><small>{chat.preview}</small>{chat.unread ? <em>{chat.unread}</em> : null}</span></span>
    </button>)}
    {!chats.length && <div className="empty-list">Ничего не найдено</div>}
  </div>
}
