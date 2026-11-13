<?php
declare(strict_types=1);
namespace App\Application\Scout;
use App\Domain\Scout\ScoutReportStore;
final readonly class GetLatestScoutReport
{
    public function __construct(private ScoutReportStore $store) {}
    public function execute(int $ownerId, array $engineMeta): array
    {
        return [
            'data' => $this->store->latest($ownerId),
            'meta' => $engineMeta,
        ];
    }
}
