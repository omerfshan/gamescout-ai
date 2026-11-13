<?php
declare(strict_types=1);
namespace App\Application\Scout;
use App\Domain\Scout\{MarketScoutRunner, ScoutReportStore, ScoutReportValidator};
final readonly class RunMarketScout
{
    public function __construct(
        private MarketScoutRunner $runner,
        private ScoutReportStore $store,
        private ScoutReportValidator $validator
    ) {}
    public function execute(int $ownerId, string $provider = 'auto', string $genre = 'all'): array
    {
        $normalizedProvider = trim($provider) !== '' ? strtolower(trim($provider)) : 'auto';
        if ($normalizedProvider === 'auto') {
            $normalizedProvider = (string) config('scout.provider', 'ollama');
        }
        if (!in_array($normalizedProvider, config('scout.allowed_providers', ['ollama']), true)) {
            throw new \InvalidArgumentException('Bu model sağlayıcısına sunucu izin vermiyor.');
        }
        $normalizedGenre = trim($genre) !== '' ? strtolower(trim($genre)) : 'all';
        $report = $this->runner->run($normalizedProvider, $normalizedGenre);
        $this->validator->validate($report);
        $saved = $this->store->save($ownerId, $report);
        return ['data' => $saved];
    }
}
