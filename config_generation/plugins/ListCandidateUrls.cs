///////////////////////////////////////////////////////////
// Plugin SMD_Plugins : file ListCandidateUrls.cs
//

using System;
using System.Collections.Generic;
using System.Text;
using System.IO;
using Sinequa.Common;
using Sinequa.Configuration;
using Sinequa.Plugins;
using Sinequa.Connectors;
using Sinequa.Indexer;
using Sinequa.Search;
using System.Text.RegularExpressions;

namespace Sinequa.Plugin
{
	public class ListCandidateUrls : ConnectorPlugin
	{

		List<UrlMetadata> urlObjList = new List<UrlMetadata>();
		string urihost = "" ;
		string collection_name;
		string seperator = "~?~";


		public override Return ApplyMappings(SinequaDoc sdoc, ConnectorDoc doc)
		{
			Sys.Log("inside ApplyMappings");
			UrlMetadata urlObj = new UrlMetadata();
			urlObj.title = Regex.Replace(doc.GetValue("linktitle"), @"\s+", " ").Trim();
			urlObj.url = doc.GetValue("urioriginalstring").Trim();
			urlObj.treepath = doc.GetValue("urirelpath").Trim();
			urlObjList.Add(urlObj);
			urihost = doc.GetValue("uriauthority").Trim();

			return base.ApplyMappings(sdoc, doc);
		}

	public override void OnConnectorEnd()
	{

        string root_path = @"C:\sinequa\data\configuration\files\customfile\candidate_urls";
        string collection_name = Connector.CollectionName;
        string path = Path.Combine(root_path, collection_name)+".txt";

        Sys.Log("root_path: ", root_path);
        Sys.Log("collection_name: ", collection_name);
		Sys.Log("file path: ", path);
		// Open a StreamWriter object to write to a text file
		using (StreamWriter writer = new StreamWriter(path))
		{

			writer.WriteLine("Website URL~?~Rel folder~?~Title");
			// Iterate through each key-value pair in the dictionary
			foreach (var obj in urlObjList)
			{
				// Write the key and value to the file, separated by a tab character
				writer.WriteLine(obj.url + seperator + obj.treepath + seperator + obj.title.Replace(System.Environment.NewLine, ""));
			}
			writer.Flush();
			writer.Dispose();
		}
	}


	}

	public class UrlMetadata
	{
		public string title {get;set;}
		public string treepath {get;set;}
		public string url {get;set;}
	}

}
