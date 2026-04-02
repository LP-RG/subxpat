module abs_diff_i600_o300(a,b,r);
input [299:0] a,b;
output [299:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
