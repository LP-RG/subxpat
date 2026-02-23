module abs_diff_i696_o348(a,b,r);
input [347:0] a,b;
output [347:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
