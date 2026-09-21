using System.Text.Json;
using System.Text.Json.Serialization;

namespace LivingDex.Core.Reference;

/// <summary>
/// An identifier that is a string on disk but a distinct type in code, so a
/// <see cref="GameId"/> cannot be passed where a <see cref="SpeciesId"/> belongs.
/// </summary>
public interface IStringId<TSelf>
    where TSelf : IStringId<TSelf>
{
    string Value { get; }

    static abstract TSelf From(string value);
}

/// <summary>Reads and writes an <see cref="IStringId{TSelf}"/> as a plain JSON string.</summary>
public sealed class StringIdJsonConverter<TId> : JsonConverter<TId>
    where TId : IStringId<TId>
{
    public override TId Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) =>
        TId.From(reader.GetString() ?? throw new JsonException($"Expected a string for {typeToConvert.Name}."));

    public override void Write(Utf8JsonWriter writer, TId value, JsonSerializerOptions options) =>
        writer.WriteStringValue(value.Value);

    public override TId ReadAsPropertyName(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) =>
        TId.From(reader.GetString() ?? throw new JsonException($"Expected a string key for {typeToConvert.Name}."));

    public override void WriteAsPropertyName(Utf8JsonWriter writer, TId value, JsonSerializerOptions options) =>
        writer.WritePropertyName(value.Value);
}

/// <summary>A single game version, for example <c>platinum</c>. Red and Blue are two ids.</summary>
[JsonConverter(typeof(StringIdJsonConverter<GameId>))]
public readonly record struct GameId(string Value) : IStringId<GameId>
{
    public static GameId From(string value) => new(value);

    public override string ToString() => Value;
}

/// <summary>A species, for example <c>chimchar</c>. Forms are <see cref="FormId"/>.</summary>
[JsonConverter(typeof(StringIdJsonConverter<SpeciesId>))]
public readonly record struct SpeciesId(string Value) : IStringId<SpeciesId>
{
    public static SpeciesId From(string value) => new(value);

    public override string ToString() => Value;
}

/// <summary>A form of a species, for example <c>vulpix-alola</c>.</summary>
[JsonConverter(typeof(StringIdJsonConverter<FormId>))]
public readonly record struct FormId(string Value) : IStringId<FormId>
{
    public static FormId From(string value) => new(value);

    public override string ToString() => Value;
}

/// <summary>An evolution chain shared by every stage in it, for example <c>chimchar</c>.</summary>
[JsonConverter(typeof(StringIdJsonConverter<EvolutionChainId>))]
public readonly record struct EvolutionChainId(string Value) : IStringId<EvolutionChainId>
{
    public static EvolutionChainId From(string value) => new(value);

    public override string ToString() => Value;
}

/// <summary>A single evolution rule, so an acquisition method can point at one.</summary>
[JsonConverter(typeof(StringIdJsonConverter<EvolutionRuleId>))]
public readonly record struct EvolutionRuleId(string Value) : IStringId<EvolutionRuleId>
{
    public static EvolutionRuleId From(string value) => new(value);

    public override string ToString() => Value;
}
