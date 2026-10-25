import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Users, Stethoscope, Building2, TestTube, Clock3, Wrench, ArrowUpRight, Plus, CalendarDays, RefreshCw } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';
import { getDashboard } from '../services/api';
import { PageHeader, Loading, ErrorState, EmptyState } from '../components/UI';
import useHospitalDataChange from '../hooks/useHospitalDataChange';

const colors = ['#56d6c8', '#63a9ff', '#a78bfa', '#f4b860', '#f17b91'];
const tooltipStyle = { backgroundColor: '#111d2b', border: '1px solid #2b3b50', borderRadius: 9, color: '#e6edf5' };

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);
  const nav = useNavigate();

  const load = useCallback((showLoading = true) => {
    if (showLoading) setBusy(true);
    getDashboard()
      .then((result) => { setData(result); setError(''); setLastUpdated(new Date()); })
      .catch((e) => setError(e.response?.data?.detail || 'The hospital data could not be reached.'))
      .finally(() => setBusy(false));
  }, []);

  useHospitalDataChange(() => load(false));

  useEffect(() => {
    load();
    const timer = window.setInterval(() => load(false), 10000);
    const onFocus = () => load(false);
    window.addEventListener('focus', onFocus);
    const onVisibility = () => { if (document.visibilityState === 'visible') load(false); };
    document.addEventListener('visibilitychange', onVisibility);
    return () => { window.clearInterval(timer); window.removeEventListener('focus', onFocus); document.removeEventListener('visibilitychange', onVisibility); };
  }, [load]);

  if (busy && !data) return <Loading label="Loading hospital dashboard..." />;
  if (error && !data) return <ErrorState message={error} retry={() => load()} />;

  const stats = [
    ['Total patients', data.total_patients, Users, '#183742', '#56d6c8'],
    ['Doctors', data.total_doctors, Stethoscope, '#1c3048', '#76a9ff'],
    ['Departments', data.total_departments, Building2, '#292548', '#b5a0ff'],
    ['Tests today', data.tests_today, TestTube, '#3c3022', '#f4b860'],
    ['Pending tests', data.pending_tests, Clock3, '#3b2b31', '#f18b9a'],
    ['Available equipment', data.available_equipment, Wrench, '#20362e', '#7bd3a9'],
  ];

  return <>
    <PageHeader eyebrow="OVERVIEW" title="Hospital dashboard" description="A clear view of today’s hospital operations."
      action={<div className="header-actions"><button className="btn btn-secondary refresh-button" onClick={() => load(false)}><RefreshCw size={15} /> Refresh</button><button className="btn btn-primary" onClick={() => nav('/patients?register=1')}><Plus size={16} /> Register patient</button></div>} />
    <div className="welcome-strip"><div><span className="welcome-icon">✦</span><div><b>Good {new Date().getHours() < 12 ? 'morning' : new Date().getHours() < 17 ? 'afternoon' : 'evening'}, {localStorage.getItem('displayName') || 'team'}</b><p>Here is your hospital overview for today.</p></div></div><span className="date-stamp"><CalendarDays size={15} />{new Date().toLocaleDateString('en-IN', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })}</span></div>
    <div className="stat-grid">{stats.map(([label, value, Icon, bg, fg]) => <div className="card stat-card" key={label}><div className="stat-top"><span>{label}</span><span className="stat-icon" style={{ background: bg, color: fg }}><Icon size={18} /></span></div><strong>{Number(value || 0).toLocaleString()}</strong><span className="stat-foot">Live hospital records</span></div>)}</div>
    <div className="chart-grid">
      <div className="card chart-card"><div className="section-title"><div><h2>Patient registrations</h2><p>Registrations over the last 7 days</p></div><span className="chart-tag"><i className="live-dot" />{lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}` : 'Live data'}</span></div>{data.patient_trend?.length ? <ResponsiveContainer width="100%" height={240}><AreaChart data={data.patient_trend} margin={{ top: 8, right: 12, left: -22, bottom: 0 }}><defs><linearGradient id="patientFill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stopColor="#56d6c8" stopOpacity={.28} /><stop offset="95%" stopColor="#56d6c8" stopOpacity={0} /></linearGradient></defs><CartesianGrid stroke="#263549" vertical={false} /><XAxis dataKey="date" axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#91a4b8' }} /><YAxis axisLine={false} tickLine={false} tick={{ fontSize: 11, fill: '#91a4b8' }} allowDecimals={false} /><Tooltip contentStyle={tooltipStyle} labelStyle={{ color: '#dce7f2' }} itemStyle={{ color: '#56d6c8' }} /><Area type="monotone" dataKey="patients" name="Patients" stroke="#56d6c8" strokeWidth={2.5} fill="url(#patientFill)" activeDot={{ r: 4, fill: '#56d6c8', stroke: '#10202e' }} /></AreaChart></ResponsiveContainer> : <EmptyState title="No registration history" />}</div>
      <div className="card chart-card"><div className="section-title"><div><h2>Patients by department</h2><p>Current patient distribution</p></div></div>{data.patients_by_department?.length ? <div className="pie-box"><ResponsiveContainer width="55%" height={205}><PieChart><Pie data={data.patients_by_department} dataKey="total" nameKey="name" innerRadius={56} outerRadius={83} paddingAngle={4}>{data.patients_by_department.map((_, i) => <Cell key={i} fill={colors[i % colors.length]} />)}</Pie><Tooltip contentStyle={tooltipStyle} itemStyle={{ color: '#e6edf5' }} /></PieChart></ResponsiveContainer><div className="legend">{data.patients_by_department.map((x, i) => <div key={x.name}><i style={{ background: colors[i % colors.length] }} />{x.name}<b>{x.total}</b></div>)}</div></div> : <EmptyState title="No departments available" />}</div>
    </div>
    <div className="lower-grid"><div className="card chart-card"><div className="section-title"><div><h2>Tests by type</h2><p>Most requested investigations</p></div><button className="text-action" onClick={() => nav('/tests')}>View all <ArrowUpRight size={14} /></button></div>{data.tests_by_type?.length ? <ResponsiveContainer width="100%" height={210}><BarChart data={data.tests_by_type} margin={{ left: -22, right: 10 }}><CartesianGrid stroke="#263549" vertical={false} /><XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#91a4b8' }} /><YAxis axisLine={false} tickLine={false} tick={{ fontSize: 10, fill: '#91a4b8' }} allowDecimals={false} /><Tooltip contentStyle={tooltipStyle} labelStyle={{ color: '#dce7f2' }} itemStyle={{ color: '#56d6c8' }} /><Bar dataKey="total" name="Tests" fill="#56d6c8" radius={[5, 5, 0, 0]} /></BarChart></ResponsiveContainer> : <EmptyState title="No tests recorded" />}</div><div className="card recent-card"><div className="section-title"><div><h2>Recently registered</h2><p>Latest patient records</p></div><button className="text-action" onClick={() => nav('/patients')}>All patients <ArrowUpRight size={14} /></button></div>{data.recent_patients?.length ? data.recent_patients.map((p) => <button className="recent-row" key={p.id} onClick={() => nav(`/patients/${p.id}`)}><div className="patient-avatar">{p.name.split(' ').map((t) => t[0]).slice(0, 2)}</div><div><b>{p.name}</b><small>{p.patient_id} · {p.department_name || 'Department pending'}</small></div><ArrowUpRight size={15} /></button>) : <EmptyState title="No patients yet" text="Register your first patient to get started." />}</div></div>
  </>;
}
