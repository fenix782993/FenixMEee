import { useEffect, useState } from 'react';
const api=(p,o={})=>fetch('/api'+p,{...o,headers:{'Content-Type':'application/json',Authorization:`Bearer ${localStorage.getItem('fenix_token')||''}`}}).then(async r=>{const d=await r.json();if(!r.ok)throw Error(d.detail||'Ошибка');return d});
export default function ContactsPanel({onClose,onOpenChat}){
 const [contacts,setContacts]=useState([]),[requests,setRequests]=useState({incoming:[],outgoing:[]}),[q,setQ]=useState(''),[people,setPeople]=useState([]),[busy,setBusy]=useState(false);
 const load=async()=>{const [c,r]=await Promise.all([api('/contacts'),api('/contacts/requests')]);setContacts(c);setRequests(r)};
 useEffect(()=>{load().catch(()=>{})},[]);
 const search=async()=>{if(q.trim().length<2)return setPeople([]);setBusy(true);try{setPeople(await api('/social/people?q='+encodeURIComponent(q.trim())))}finally{setBusy(false)}};
 const add=async id=>{await api('/contacts',{method:'POST',body:JSON.stringify({user_id:id})});await load();setPeople([]);setQ('')};
 const friend=async id=>{await api('/contacts/request',{method:'POST',body:JSON.stringify({user_id:id})});await load();setPeople([]);setQ('')};
 const respond=async(id,accept)=>{const d=await api('/contacts/request/respond',{method:'POST',body:JSON.stringify({request_id:id,accept})});await load();if(d.chat_id)onOpenChat?.(d.chat_id)};
 return <div className="modal-layer"><div className="contacts-card"><header><div><h2>Контакты</h2><small>Ваши друзья и сохранённые контакты</small></div><button onClick={onClose}>×</button></header>
 <div className="contact-search"><input value={q} onChange={e=>setQ(e.target.value)} onKeyDown={e=>e.key==='Enter'&&search()} placeholder="Найти по имени или @username"/><button onClick={search}>{busy?'…':'⌕'}</button></div>
 {requests.incoming.length>0&&<section><h3>Запросы в друзья</h3>{requests.incoming.map(r=><div className="contact-item" key={r.id}><div className="avatar">{r.from.display_name?.[0]}</div><div><b>{r.from.display_name}</b><small>@{r.from.username}</small></div><button className="primary mini" onClick={()=>respond(r.id,true)}>Принять</button><button className="secondary mini" onClick={()=>respond(r.id,false)}>Отклонить</button></div>)}</section>}
 {people.length>0&&<section><h3>Результаты поиска</h3>{people.map(p=><div className="contact-item" key={p.id}><div className="avatar">{p.display_name?.[0]}</div><div className="contact-main"><b>{p.display_name}</b><small>@{p.username} · ID {p.public_code||p.id}</small></div><button className="secondary mini" onClick={()=>friend(p.id)}>＋ Друг</button><button className="primary mini" onClick={()=>add(p.id)}>Добавить</button></div>)}</section>}
 <section><h3>Мои контакты · {contacts.length}</h3>{contacts.length?contacts.map(c=><div className="contact-item" key={c.id} onDoubleClick={()=>onOpenChat?.(c.id)}><div className="avatar">{c.display_name?.[0]}</div><div className="contact-main"><b>{c.nickname||c.display_name}</b><small>@{c.username} · {c.online?'в сети':'не в сети'}</small></div><button className="secondary mini" onClick={()=>onOpenChat?.(c.id)}>Написать</button></div>):<div className="contact-empty">Пока нет контактов.<br/>Найди пользователя выше и добавь его сюда.</div>}</section>
 </div></div>
}
