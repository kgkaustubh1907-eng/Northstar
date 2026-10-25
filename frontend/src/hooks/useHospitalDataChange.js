import { useEffect, useRef } from 'react';

export default function useHospitalDataChange(onChange) {
  const callback = useRef(onChange);
  callback.current = onChange;

  useEffect(() => {
    const handleChange = () => callback.current?.();
    window.addEventListener('hospital:data-changed', handleChange);
    return () => window.removeEventListener('hospital:data-changed', handleChange);
  }, []);
}
