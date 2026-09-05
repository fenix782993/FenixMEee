export default function Toast({text,onClose}){if(!text)return null;return <div className="toast" onClick={onClose}>{text}</div>}
