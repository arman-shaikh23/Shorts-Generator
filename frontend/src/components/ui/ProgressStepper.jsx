import { motion } from 'framer-motion';
import { CheckCircle2, Loader2 } from 'lucide-react';
import { cn } from '../../lib/utils';

export function ProgressStepper({ steps, currentStep, isProcessing }) {
  if (!steps || steps.length === 0) return null;

  return (
    <div className="space-y-1">
      {steps.map((step, index) => {
        const isActive = currentStep?.label === step.label && isProcessing;
        const isDone = step.status === 'done' || (!isActive && index < steps.length - 1 && steps[index + 1]);

        return (
          <motion.div
            key={step.label}
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: index * 0.05 }}
            className={cn(
              'flex items-center gap-4 px-4 py-3 rounded-xl transition-all duration-300',
              isActive && 'bg-blue-500/10 border border-blue-500/20',
              isDone && !isActive && 'opacity-60',
            )}
          >
            <div className="w-8 h-8 rounded-full flex items-center justify-center text-sm shrink-0">
              {isDone && !isActive ? (
                <CheckCircle2 size={20} className="text-green-400" />
              ) : isActive ? (
                <Loader2 size={20} className="text-blue-400 animate-spin" />
              ) : (
                <span className="text-lg">{step.icon}</span>
              )}
            </div>

            <div className="flex-1 min-w-0">
              <p className={cn('font-medium text-sm', isActive ? 'text-white' : 'text-gray-400')}>
                {step.label}
              </p>
              <p className="text-xs text-gray-500 truncate">{step.description}</p>
            </div>

            {isActive && (
              <div className="flex gap-1">
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" />
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" style={{ animationDelay: '0.2s' }} />
                <span className="w-1.5 h-1.5 rounded-full bg-blue-400 animate-pulse" style={{ animationDelay: '0.4s' }} />
              </div>
            )}
          </motion.div>
        );
      })}
    </div>
  );
}
