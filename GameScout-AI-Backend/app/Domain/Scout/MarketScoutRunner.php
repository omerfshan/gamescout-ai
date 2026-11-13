<?php
declare(strict_types=1);
namespace App\Domain\Scout;
interface MarketScoutRunner
{
    public function run(string $provider = 'ollama', string $genre = 'all'): array;
}
