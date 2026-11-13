<?php
declare(strict_types=1);
namespace Tests;
abstract class TestCase extends \Illuminate\Foundation\Testing\TestCase
{
    public $mockConsoleOutput = false;
    public function withToken(string $token, string $type = 'Bearer')
    {
        if ($this->app !== null && $this->app->bound('auth')) {
            $this->app['auth']->forgetGuards();
        }
        return parent::withToken($token, $type);
    }
}
