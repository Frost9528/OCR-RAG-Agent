import { Settings, MessageCircle, HelpCircle } from 'lucide-react';
import { Button } from './ui/button';
import { useToast } from '@/hooks/use-toast';

export function Header() {
  const { toast } = useToast();

  const handleComingSoon = () => {
    toast({ description: '功能开发中，敬请期待' });
  };

  return (
    <header className="border-b border-border bg-card/80 backdrop-blur-sm px-6 py-4 flex items-center justify-between shadow-sm">
      <h1 className="bg-gradient-to-r from-primary via-purple-500 to-accent bg-clip-text text-transparent">
        Agentic RAG 系统
      </h1>

      <div className="flex items-center gap-2">
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-primary transition-colors"
          onClick={handleComingSoon}
          title="设置"
        >
          <Settings className="h-5 w-5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-primary transition-colors"
          onClick={handleComingSoon}
          title="会话"
        >
          <MessageCircle className="h-5 w-5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-primary transition-colors"
          onClick={handleComingSoon}
          title="帮助"
        >
          <HelpCircle className="h-5 w-5" />
        </Button>
      </div>
    </header>
  );
}
