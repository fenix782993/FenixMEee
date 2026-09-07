
import { useEffect, useMemo, useState } from 'react';
import AuthScreen from './features/auth/AuthScreen';
import ChatList from './features/chats/ChatList';
import ChatView from './features/chats/ChatView';
import ProfilePanel from './features/profile/ProfilePanel';
import SettingsPanel from './features/settings/SettingsPanel';
import GroupModal from './features/groups/GroupModal';
import './styles.css';

const demoChats = [
  { id: 1, title: 'Избранное', preview: 'Сохранённые сообщения', time: '18:42', unread: 0, avatar: '★' },
  { id: 2, title: 'Fenix Team', preview: 'Новый релиз готов', time: '18:31', unread: 3, avatar: 'F' },
  { id: 3, title: 'Александр', preview: 'Давай созвонимся вечером', time: '17:58', unread: 0, avatar: 'A' },
  { id: 4, title: 'Дизайн Fenix', preview: 'Макеты обновлены', time: '16:20', unread: 12, avatar: 'D' },
];

export default function App() {
  const [authed, setAuthed] = useState(Boolean(localStorage.getItem('fenix_token')));
  const [active, setActive] = useState(2);
  const [panel, setPanel] = useState(null);
  const [search, setSearch] = useState('');
  const [mobile, setMobile] = useState(false);
  const [groupOpen, setGroupOpen] = useState(false);

  useEffect(() => {
    const onResize = () => setMobile(window.innerWidth < 760);
    onResize();
    window.addEventListener('resize', onResize);
    return () => window.removeEventListener('resize', onResize);
  }, []);

  const chats = useMemo(
    () => demoChats.filter(c => c.title.toLowerCase().includes(search.toLowerCase()) ||
      c.preview.toLowerCase().includes(search.toLowerCase())),
    [search]
  );

  if (!authed) return <AuthScreen onAuthenticated={() => setAuthed(true)} />;

  return (
    <div className={`fenix-shell ${mobile ? 'is-mobile' : ''}`}>
      <aside className={`fenix-sidebar ${mobile && active ? 'mobile-hidden' : ''}`}>
        <div className="sidebar-top">
          <button className="round-icon" onClick={() => setPanel(panel === 'menu' ? null : 'menu')}>☰</button>
          <div className="brand"><span className="brand-mark">✦</span><span>Fenix</span></div>
          <button className="round-icon" onClick={() => setGroupOpen(true)}>＋</button>
        </div>
        <div className="search-box">
          <span>⌕</span>
          <input value={search} onChange={e => setSearch(e.target.value)} placeholder="Поиск" />
          <kbd>Ctrl K</kbd>
        </div>
        <div className="folder-row">
          <button className="folder active">Все чаты</button>
          <button className="folder">Личные</button>
          <button className="folder">Работа</button>
        </div>
        <div className="stories">
          <div className="story add">＋</div><div className="story">F</div><div className="story">A</div><div className="story">D</div>
        </div>
        <ChatList chats={chats} active={active} onSelect={setActive} />
        <div className="sidebar-bottom">
          <button onClick={() => setPanel('profile')}>👤 Профиль</button>
          <button onClick={() => setPanel('settings')}>⚙ Настройки</button>
        </div>
      </aside>

      <main className={`fenix-main ${mobile && !active ? 'mobile-hidden' : ''}`}>
        <ChatView chat={chats.find(c => c.id === active) || demoChats[1]} onBack={() => setActive(0)} />
      </main>

      {panel === 'profile' && <ProfilePanel onClose={() => setPanel(null)} />}
      {panel === 'settings' && <SettingsPanel onClose={() => setPanel(null)} />}
      {panel === 'menu' && (
        <div className="overlay-panel">
          <div className="side-menu">
            <div className="menu-user"><div className="avatar large">F</div><b>Fenix User</b><small>@fenix</small></div>
            <button>🔖 Избранное</button><button>👥 Контакты</button><button>📁 Папки</button><button>📞 Звонки</button>
            <button>🔔 Уведомления</button><button>🎨 Оформление</button><button onClick={() => setPanel('settings')}>⚙ Настройки</button>
          </div>
          <div className="menu-backdrop" onClick={() => setPanel(null)} />
        </div>
      )}
      {groupOpen && <GroupModal onClose={() => setGroupOpen(false)} />}
    </div>
  );
}
