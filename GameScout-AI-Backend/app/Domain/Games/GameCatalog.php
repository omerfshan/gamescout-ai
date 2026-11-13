<?php
declare(strict_types=1);
namespace App\Domain\Games;
interface GameCatalog
{
    /** @param list<GameData> $games Number of newly inserted records. */
    public function import(int $ownerId, array $games): int;
    /** @return list<GameData> */
    public function list(int $ownerId, ?string $platform): array;
}
