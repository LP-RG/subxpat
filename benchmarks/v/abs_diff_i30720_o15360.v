module abs_diff_i30720_o15360(a,b,r);
input [15359:0] a,b;
output [15359:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
