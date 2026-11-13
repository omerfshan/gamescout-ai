<?php
declare(strict_types=1);
namespace App\Application\Scout;
use App\Domain\Scout\{MarketScoutRunner, ScoutReportStore};
final readonly class RunMarketScout
{
    public function __construct(
        private MarketScoutRunner $runner,
        private ScoutReportStore $store
    ) {}
    public function execute(int $ownerId, string $provider = 'auto'): array
    {
        $normalizedProvider = trim($provider) !== '' ? strtolower(trim($provider)) : 'auto';
        $report = $this->runner->run($normalizedProvider);
        if (
            !isset($report['scan_id']) ||
            !isset($report['actionable_game_proposals']) ||
            !is_array($report['actionable_game_proposals']) ||
            !isset($report['top_genre_insights']) ||
            !is_array($report['top_genre_insights'])
        ) {
            throw new \RuntimeException('Pazar keşif raporu geçersiz formatta döndü.');
        }
        $saved = $this->store->save($ownerId, $report);
        return ['data' => $saved];
    }
}
