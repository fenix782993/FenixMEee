export function formatTime(value){return new Date(value).toLocaleTimeString([], {hour:'2-digit',minute:'2-digit'})}
export function formatDate(value){return new Date(value).toLocaleDateString('ru-RU',{day:'numeric',month:'long',year:'numeric'})}
export function initials(value=''){return value.split(/\s+/).map(x=>x[0]).join('').slice(0,2).toUpperCase()}
