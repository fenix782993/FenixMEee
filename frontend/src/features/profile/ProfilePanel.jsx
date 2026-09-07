
export default function ProfilePanel({onClose}) {
  return <div className="modal-layer"><div className="modal-card profile-card"><button className="close" onClick={onClose}>×</button><div className="profile-hero"><div className="avatar profile-avatar">F</div><h2>Fenix User</h2><p>@fenix</p></div><div className="info-row"><b>Имя пользователя</b><span>@fenix</span></div><div className="info-row"><b>ID</b><span>73800001</span></div><div className="info-row"><b>Статус</b><span>В сети</span></div><button className="primary wide">Изменить профиль</button></div></div>
}
