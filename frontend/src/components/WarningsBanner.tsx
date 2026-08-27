import React from 'react';
import { AlertTriangle } from 'lucide-react';

interface WarningsBannerProps {
  warnings: string[];
}

export const WarningsBanner: React.FC<WarningsBannerProps> = ({ warnings }) => {
  if (!warnings || warnings.length === 0) return null;

  return (
    <div className="mb-6 space-y-2.5">
      {warnings.map((warn, index) => (
        <div
          key={index}
          className="p-4 bg-amber-50 border border-amber-300 rounded-xl flex items-start space-x-3 text-amber-900 text-sm shadow-sm"
        >
          <AlertTriangle className="w-5 h-5 text-amber-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <span className="font-bold block text-xs uppercase tracking-wider text-amber-800">
              Aviso Importante:
            </span>
            <p className="mt-0.5 text-xs text-amber-900 font-medium leading-relaxed">
              {warn}
            </p>
          </div>
        </div>
      ))}
    </div>
  );
};
