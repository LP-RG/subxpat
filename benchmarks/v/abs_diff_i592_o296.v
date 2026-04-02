module abs_diff_i592_o296(a,b,r);
input [295:0] a,b;
output [295:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
