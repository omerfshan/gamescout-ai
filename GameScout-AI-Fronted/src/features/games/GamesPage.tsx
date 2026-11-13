import type { AuthUser } from '../../domain/auth';
import { OpportunityScoutPanel } from '../scout/OpportunityScoutPanel';

interface Props {
  user: AuthUser;
  onLogout: () => Promise<void>;
}

export function GamesPage(_props: Props) {
  return <OpportunityScoutPanel />;
}
