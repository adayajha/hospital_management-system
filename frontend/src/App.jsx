import { useEffect, useState } from 'react';
import { api } from './api';

const blankTicket = { subject: '', description: '', category: 'it_issue', priority: 'medium', department_id: '' };
const labels = { equipment_issue: 'Equipment issue', maintenance: 'Maintenance', it_issue: 'IT issue', facility_request: 'Facility request' };

function Login({ onLogin }) {
  const [form, setForm] = useState({ email: 'admin@hospital.local', password: 'Admin123!' });
  const [error, setError] = useState('');
  async function submit(e) { e.preventDefault(); try { const result = await api('/auth/login', { method: 'POST', body: JSON.stringify(form) }); localStorage.setItem('hsrs_token', result.access_token); onLogin(result.user); } catch (err) { setError(err.message); } }
  return <main className="auth"><section><h1>Hospital Support</h1><p>Request and manage hospital support services.</p><form onSubmit={submit}><label>Email<input type="email" value={form.email} onChange={e => setForm({...form, email:e.target.value})} required /></label><label>Password<input type="password" value={form.password} onChange={e => setForm({...form, password:e.target.value})} required /></label>{error && <p className="error">{error}</p>}<button>Sign in</button></form><small>Development admin: admin@hospital.local / Admin123!</small></section></main>;
}

function TicketForm({ departments, onCreated }) {
  const [form, setForm] = useState(blankTicket); const [error, setError] = useState('');
  async function submit(e) { e.preventDefault(); try { await api('/tickets', {method:'POST', body:JSON.stringify(form)}); setForm(blankTicket); onCreated(); } catch(err) { setError(err.message); } }
  return <form className="ticket-form" onSubmit={submit}><h2>New support request</h2><input placeholder="Brief subject" value={form.subject} onChange={e=>setForm({...form,subject:e.target.value})} required /><select value={form.category} onChange={e=>setForm({...form,category:e.target.value})}>{Object.entries(labels).map(([key,label])=><option key={key} value={key}>{label}</option>)}</select><select value={form.priority} onChange={e=>setForm({...form,priority:e.target.value})}>{['low','medium','high','critical'].map(x=><option key={x}>{x}</option>)}</select><select value={form.department_id} onChange={e=>setForm({...form,department_id:e.target.value})} required><option value="">Select department</option>{departments.map(d=><option key={d.id} value={d.id}>{d.name}</option>)}</select><textarea placeholder="Describe the issue, exact location and urgency" value={form.description} onChange={e=>setForm({...form,description:e.target.value})} required />{error && <p className="error">{error}</p>}<button>Create request</button></form>;
}

function App() {
  const [user, setUser] = useState(null), [tickets, setTickets] = useState([]), [departments, setDepartments] = useState([]), [selected, setSelected] = useState(null), [error, setError] = useState(''), [filter, setFilter] = useState('');
  async function load() { try { const [ticketData, departmentData] = await Promise.all([api(`/tickets${filter ? `?status=${filter}` : ''}`), api('/departments')]); setTickets(ticketData.items); setDepartments(departmentData.items); } catch(err) { setError(err.message); } }
  useEffect(() => { if (localStorage.getItem('hsrs_token')) api('/auth/me').then(r => setUser(r.user)).catch(() => localStorage.removeItem('hsrs_token')); }, []);
  useEffect(() => { if(user) load(); }, [user, filter]);
  async function details(id) { try { setSelected(await api(`/tickets/${id}`)); } catch(err) { setError(err.message); } }
  async function addComment(e) { e.preventDefault(); const message = new FormData(e.target).get('message'); if (!message) return; try { await api(`/tickets/${selected.ticket.id}/comments`, {method:'POST', body:JSON.stringify({message})}); e.target.reset(); details(selected.ticket.id); } catch(err) { setError(err.message); } }
  async function setStatus(status) { try { const resolution_note = status === 'resolved' ? prompt('Resolution note:') : undefined; if (status === 'resolved' && !resolution_note) return; await api(`/tickets/${selected.ticket.id}/status`, {method:'PATCH', body:JSON.stringify({status, resolution_note})}); await load(); details(selected.ticket.id); } catch(err) { setError(err.message); } }
  if (!user) return <Login onLogin={setUser} />;
  return <main><header><div><h1>Hospital Support Request System</h1><p>{user.full_name} · {user.role}</p></div><button className="secondary" onClick={()=>{localStorage.removeItem('hsrs_token');setUser(null)}}>Sign out</button></header>{error && <p className="error banner">{error}</p>}<div className="layout"><aside><TicketForm departments={departments} onCreated={load} /></aside><section className="tickets"><div className="toolbar"><h2>Support requests</h2><select value={filter} onChange={e=>setFilter(e.target.value)}><option value="">All statuses</option>{['open','assigned','in_progress','resolved','closed','reopened'].map(s=><option key={s}>{s}</option>)}</select></div>{tickets.length === 0 ? <p>No tickets found.</p> : <table><thead><tr><th>Ticket</th><th>Category</th><th>Priority</th><th>Status</th><th></th></tr></thead><tbody>{tickets.map(t=><tr key={t.id}><td><strong>{t.ticket_number}</strong><br/>{t.subject}</td><td>{labels[t.category]}</td><td><span className={`pill ${t.priority}`}>{t.priority}</span></td><td>{t.status.replace('_',' ')}</td><td><button className="secondary" onClick={()=>details(t.id)}>View</button></td></tr>)}</tbody></table>}</section></div>{selected && <div className="modal"><section><button className="close" onClick={()=>setSelected(null)}>×</button><h2>{selected.ticket.ticket_number}: {selected.ticket.subject}</h2><p>{selected.ticket.description}</p><p><b>Status:</b> {selected.ticket.status} · <b>Priority:</b> {selected.ticket.priority}</p>{['admin','agent'].includes(user.role) && <div className="actions"><button onClick={()=>setStatus('in_progress')}>Start work</button><button onClick={()=>setStatus('resolved')}>Resolve</button></div>}<h3>Comments</h3>{selected.comments.map(c=><article key={c.id}><b>{c.author_name}</b><p>{c.message}</p></article>)}<form onSubmit={addComment} className="comment"><input name="message" placeholder="Add an update" /><button>Send</button></form></section></div>}</main>;
}

export default App;
