<?php
declare(strict_types=1);
namespace App\Providers;
use Illuminate\Support\ServiceProvider;
use App\Domain\Auth\UserAuthenticator;
use App\Domain\Games\GameCatalog;
use App\Domain\Scout\{MarketScoutRunner, ScoutReportStore};
use App\Infrastructure\Auth\SanctumUserAuthenticator;
use App\Infrastructure\Games\PgsqlGameCatalog;
use App\Infrastructure\Scout\{DbScoutReportStore, PythonCliMarketScoutRunner};
final class AppServiceProvider extends ServiceProvider
{
    public function register(): void
    {
        $this->app->bind(GameCatalog::class, PgsqlGameCatalog::class);
        $this->app->bind(UserAuthenticator::class, SanctumUserAuthenticator::class);
        $this->app->bind(ScoutReportStore::class, DbScoutReportStore::class);
        $this->app->bind(MarketScoutRunner::class, PythonCliMarketScoutRunner::class);
    }
}
