module abs_diff_i1004_o502(a,b,r);
input [501:0] a,b;
output [501:0] r;

assign r = (a>b) ? (a-b) : (b-a);

endmodule
