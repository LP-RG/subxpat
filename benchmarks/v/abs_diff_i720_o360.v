module abs_diff_i720_o360(a,b,r);
input [359:0] a,b;
output [359:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
