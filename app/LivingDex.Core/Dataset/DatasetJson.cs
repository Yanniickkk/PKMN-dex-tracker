using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace LivingDex.Core.Dataset;

/// <summary>
/// The single JSON configuration used for reading and writing the dataset. The pipeline writes
/// with it and the app reads with it, so the two cannot drift.
/// </summary>
public static class DatasetJson
{
    /// <summary>
    /// Indented and camel-cased on purpose: the dataset is committed, so a rebuild has to produce
    /// a readable diff rather than one enormous line.
    /// </summary>
    public static JsonSerializerOptions Options { get; } = Create();

    private static JsonSerializerOptions Create()
    {
        var options = new JsonSerializerOptions
        {
            PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
            DictionaryKeyPolicy = JsonNamingPolicy.CamelCase,
            DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
            WriteIndented = true,
            // Reflection-based rather than source-generated: trimming is off anyway, and the
            // polymorphic acquisition and filter hierarchies stay far easier to extend this way.
            TypeInfoResolver = new DefaultJsonTypeInfoResolver(),
            NewLine = "\n",
        };

        options.Converters.Add(new JsonStringEnumConverter(JsonNamingPolicy.CamelCase));
        options.MakeReadOnly();
        return options;
    }
}
