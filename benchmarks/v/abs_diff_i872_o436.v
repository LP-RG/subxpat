module abs_diff_i872_o436(a,b,r);
input [435:0] a,b;
output [435:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
