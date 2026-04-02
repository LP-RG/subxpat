module abs_diff_i504_o252(a,b,r);
input [251:0] a,b;
output [251:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
