<?php
declare(strict_types=1);
namespace App\Domain\Scout;
interface ScoutReportStore
{
    public function save(int $ownerId, array $reportPayload): array;
    public function latest(int $ownerId): ?array;
}
