import { useState, useEffect } from 'react';
import './App.css';

/* ── Constants ──────────────────────────────────────────────── */
const STEPS = ['Account', 'Personal', 'Preferences', 'Review'];
const STORAGE_KEY = 'reg_form_data';

const INIT = {
  email: '', password: '', confirmPassword: '',
  firstName: '', lastName: '', phone: '',
  role: '', newsletter: false,
};

/* ── Helpers ────────────────────────────────────────────────── */
function passwordStrength(pw) {
  if (!pw) return 0;
  let score = 0;
  if (pw.length >= 8)            score++;
  if (/[A-Z]/.test(pw))         score++;
  if (/[0-9]/.test(pw))         score++;
  if (/[^A-Za-z0-9]/.test(pw))  score++;
  return score;
}

const strengthLabel = ['', 'Weak', 'Fair', 'Good', 'Strong'];
const strengthClass  = ['', 's1',   's2',   's3',   's4'];

function validate(step, data) {
  const errors = {};
  if (step === 0) {
    if (!data.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email))
      errors.email = 'Enter a valid email address.';
    if (!data.password || data.password.length < 8)
      errors.password = 'Password must be at least 8 characters.';
    if (data.password !== data.confirmPassword)
      errors.confirmPassword = 'Passwords do not match.';
  }
  if (step === 1) {
    if (!data.firstName.trim()) errors.firstName = 'First name is required.';
    if (!data.lastName.trim())  errors.lastName  = 'Last name is required.';
    if (data.phone && !/^\+?[\d\s\-]{7,15}$/.test(data.phone))
      errors.phone = 'Enter a valid phone number.';
  }
  if (step === 2) {
    if (!data.role) errors.role = 'Please select a role.';
  }
  return errors;
}

/* ── ProgressBar ────────────────────────────────────────────── */
function ProgressBar({ current, total }) {
  const pct = ((current) / total) * 100;
  return (
    <div className="progress-header">
      <div className="step-labels">
        {STEPS.map((s, i) => (
          <span key={s} className={i === current ? 'active' : ''}>{s}</span>
        ))}
      </div>
      <div className="progress-bar-track">
        <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <div className="step-counter">Step {current + 1} of {total}</div>
    </div>
  );
}

/* ── Step 0 – Account ───────────────────────────────────────── */
function StepAccount({ data, onChange, errors }) {
  const strength = passwordStrength(data.password);
  return (
    <>
      <div className="step-title">Create your account</div>
      <div className="step-subtitle">Set up your login credentials.</div>

      <div className="field">
        <label htmlFor="email">Email</label>
        <input
          id="email" type="email" placeholder="you@example.com"
          value={data.email}
          className={errors.email ? 'err' : data.email ? 'ok' : ''}
          onChange={e => onChange('email', e.target.value)}
        />
        {errors.email && <div className="hint err">{errors.email}</div>}
      </div>

      <div className="field">
        <label htmlFor="password">Password</label>
        <input
          id="password" type="password" placeholder="Min. 8 characters"
          value={data.password}
          className={errors.password ? 'err' : data.password.length >= 8 ? 'ok' : ''}
          onChange={e => onChange('password', e.target.value)}
        />
        {data.password && (
          <>
            <div className="strength-track">
              {[1,2,3,4].map(n => (
                <span key={n} className={strength >= n ? strengthClass[strength] : ''} />
              ))}
            </div>
            <div className="strength-label">{strengthLabel[strength]}</div>
          </>
        )}
        {errors.password && <div className="hint err">{errors.password}</div>}
      </div>

      <div className="field">
        <label htmlFor="confirmPassword">Confirm Password</label>
        <input
          id="confirmPassword" type="password" placeholder="Repeat password"
          value={data.confirmPassword}
          className={errors.confirmPassword ? 'err' : data.confirmPassword && data.confirmPassword === data.password ? 'ok' : ''}
          onChange={e => onChange('confirmPassword', e.target.value)}
        />
        {errors.confirmPassword && <div className="hint err">{errors.confirmPassword}</div>}
      </div>
    </>
  );
}

/* ── Step 1 – Personal ──────────────────────────────────────── */
function StepPersonal({ data, onChange, errors }) {
  return (
    <>
      <div className="step-title">Personal details</div>
      <div className="step-subtitle">Tell us a little about yourself.</div>

      <div className="field">
        <label htmlFor="firstName">First Name</label>
        <input
          id="firstName" type="text" placeholder="John"
          value={data.firstName}
          className={errors.firstName ? 'err' : data.firstName ? 'ok' : ''}
          onChange={e => onChange('firstName', e.target.value)}
        />
        {errors.firstName && <div className="hint err">{errors.firstName}</div>}
      </div>

      <div className="field">
        <label htmlFor="lastName">Last Name</label>
        <input
          id="lastName" type="text" placeholder="Doe"
          value={data.lastName}
          className={errors.lastName ? 'err' : data.lastName ? 'ok' : ''}
          onChange={e => onChange('lastName', e.target.value)}
        />
        {errors.lastName && <div className="hint err">{errors.lastName}</div>}
      </div>

      <div className="field">
        <label htmlFor="phone">Phone <span style={{fontWeight:300}}>(optional)</span></label>
        <input
          id="phone" type="tel" placeholder="+1 234 567 8900"
          value={data.phone}
          className={errors.phone ? 'err' : ''}
          onChange={e => onChange('phone', e.target.value)}
        />
        {errors.phone && <div className="hint err">{errors.phone}</div>}
      </div>
    </>
  );
}

/* ── Step 2 – Preferences ───────────────────────────────────── */
function StepPreferences({ data, onChange, errors }) {
  return (
    <>
      <div className="step-title">Preferences</div>
      <div className="step-subtitle">Customize your experience.</div>

      <div className="field">
        <label htmlFor="role">I am a…</label>
        <select
          id="role"
          value={data.role}
          className={errors.role ? 'err' : ''}
          onChange={e => onChange('role', e.target.value)}
        >
          <option value="">Select a role</option>
          <option value="Student">Student</option>
          <option value="Developer">Developer</option>
          <option value="Designer">Designer</option>
          <option value="Manager">Manager</option>
          <option value="Other">Other</option>
        </select>
        {errors.role && <div className="hint err">{errors.role}</div>}
      </div>

      <div className="field" style={{ display:'flex', alignItems:'center', gap:'0.7rem' }}>
        <input
          id="newsletter" type="checkbox"
          checked={data.newsletter}
          onChange={e => onChange('newsletter', e.target.checked)}
          style={{ width:'auto', cursor:'pointer', accentColor:'var(--accent)' }}
        />
        <label htmlFor="newsletter" style={{ textTransform:'none', fontSize:'0.88rem', cursor:'pointer', marginBottom:0 }}>
          Send me product updates &amp; tips
        </label>
      </div>
    </>
  );
}

/* ── Step 3 – Review ────────────────────────────────────────── */
function StepReview({ data }) {
  return (
    <>
      <div className="step-title">Review &amp; submit</div>
      <div className="step-subtitle">Double-check your info before finishing.</div>
      <div className="review-box">
        {[
          ['Email',       data.email],
          ['First Name',  data.firstName],
          ['Last Name',   data.lastName],
          ['Phone',       data.phone || '—'],
          ['Role',        data.role],
          ['Newsletter',  data.newsletter ? 'Yes' : 'No'],
        ].map(([k, v]) => (
          <div key={k} className="review-row">
            <span>{k}</span>
            <span>{v}</span>
          </div>
        ))}
      </div>
    </>
  );
}

/* ── Success ────────────────────────────────────────────────── */
function SuccessScreen({ name, onRestart }) {
  return (
    <div className="success-screen">
      <div className="success-icon">🎉</div>
      <h2>Welcome, {name}!</h2>
      <p>Your account has been created. All data has been saved to local storage.</p>
      <button className="restart-btn" onClick={onRestart}>Start over</button>
    </div>
  );
}

/* ── App ────────────────────────────────────────────────────── */
export default function App() {
  const [step, setStep]     = useState(0);
  const [data, setData]     = useState(() => {
    try { return { ...INIT, ...JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}') }; }
    catch { return INIT; }
  });
  const [errors, setErrors] = useState({});
  const [done,  setDone]    = useState(false);

  // Persist to localStorage on every data change
  useEffect(() => {
    const { password, confirmPassword, ...safe } = data;
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...safe, password: '***' }));
  }, [data]);

  function handleChange(field, value) {
    setData(prev => ({ ...prev, [field]: value }));
    if (errors[field]) setErrors(prev => ({ ...prev, [field]: '' }));
  }

  function handleNext() {
    const errs = validate(step, data);
    if (Object.keys(errs).length) { setErrors(errs); return; }
    setErrors({});
    if (step < STEPS.length - 1) setStep(s => s + 1);
  }

  function handleBack() { setErrors({}); setStep(s => s - 1); }

  function handleSubmit() {
    localStorage.setItem(STORAGE_KEY, JSON.stringify({ ...data, password: '***', confirmedAt: new Date().toISOString() }));
    setDone(true);
  }

  function handleRestart() {
    localStorage.removeItem(STORAGE_KEY);
    setData(INIT);
    setStep(0);
    setErrors({});
    setDone(false);
  }

  const stepComponents = [
    <StepAccount     data={data} onChange={handleChange} errors={errors} />,
    <StepPersonal    data={data} onChange={handleChange} errors={errors} />,
    <StepPreferences data={data} onChange={handleChange} errors={errors} />,
    <StepReview      data={data} />,
  ];

  const isLast = step === STEPS.length - 1;

  return (
    <div className="card">
      {done ? (
        <SuccessScreen name={data.firstName || 'there'} onRestart={handleRestart} />
      ) : (
        <>
          <ProgressBar current={step} total={STEPS.length} />
          {stepComponents[step]}
          <div className="btn-row">
            {step > 0 && (
              <button id="btn-back" className="btn btn-secondary" onClick={handleBack}>Back</button>
            )}
            {isLast ? (
              <button id="btn-submit" className="btn btn-primary" onClick={handleSubmit}>Submit ✓</button>
            ) : (
              <button id="btn-next" className="btn btn-primary" onClick={handleNext}>Next →</button>
            )}
          </div>
        </>
      )}
    </div>
  );
}
