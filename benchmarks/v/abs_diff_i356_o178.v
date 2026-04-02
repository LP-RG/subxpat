module abs_diff_i356_o178(a,b,r);
input [177:0] a,b;
output [177:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
