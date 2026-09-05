export default function IconButton({children,title,onClick,active=false}){return <button className={`icon-btn ${active?'active':''}`} title={title} onClick={onClick}>{children}</button>}
