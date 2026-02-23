module abs_diff_i500_o250(a,b,r);
input [249:0] a,b;
output [249:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
