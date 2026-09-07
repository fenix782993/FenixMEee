
import {useState} from 'react';
export default function GroupModal({onClose}) {
 const [name,setName]=useState('');
 return <div className="modal-layer"><div className="modal-card"><button className="close" onClick={onClose}>×</button><h2>Создать группу</h2><div className="group-icon">👥</div><input className="text-input" value={name} onChange={e=>setName(e.target.value)} placeholder="Название группы"/><button className="primary wide" disabled={!name.trim()}>Создать группу</button><button className="secondary wide" onClick={onClose}>Отмена</button></div></div>
}
