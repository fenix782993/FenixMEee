
import {useState} from 'react';
export default function SettingsPanel({onClose}) {
 const [dark,setDark]=useState(true),[sound,setSound]=useState(true);
 return <div className="modal-layer"><div className="modal-card settings-card"><button className="close" onClick={onClose}>×</button><h2>Настройки</h2><p className="muted">Fenix Messenger · Desktop / Mobile</p>
 <section><h4>Основные</h4><label>Тёмная тема <input type="checkbox" checked={dark} onChange={e=>setDark(e.target.checked)}/></label><label>Звуки <input type="checkbox" checked={sound} onChange={e=>setSound(e.target.checked)}/></label><label>Анимации <input type="checkbox" defaultChecked/></label></section>
 <section><h4>Конфиденциальность</h4><button className="setting-btn">Последний визит <span>Мои контакты ›</span></button><button className="setting-btn">Звонки <span>Мои контакты ›</span></button></section>
 <section><h4>Данные</h4><button className="setting-btn">Автозагрузка медиа <span>Wi‑Fi ›</span></button><button className="setting-btn">Хранилище <span>Управление ›</span></button></section>
 </div></div>
}
