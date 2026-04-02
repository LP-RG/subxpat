module abs_diff_i840_o420(a,b,r);
input [419:0] a,b;
output [419:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
